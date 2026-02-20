from .utils import WORLD_CHR_MAN_PATTERN
from .entity import Entity
import ds3_open as open
import pymem
import psutil
import time

class DS3Reader:
    def __init__(self, enemy, debug=False):
        self.debug = debug
        self.enemy = enemy
        self.ds3 = None
        self.module = None
        self.pid = None
        self.world_chr_man = None
        self._player = None
        self._boss = None

    def _current_ds3_pid(self):
        for p in psutil.process_iter(["pid", "name"]):
            if (p.info["name"] or "").lower() == "darksoulsiii.exe":
                return p.info["pid"]
        return None

    def _detach(self):
        try:
            if self.ds3 is not None:
                try:
                    self.ds3.close_process()
                except Exception:
                    pass
        finally:
            self.ds3 = None
            self.module = None
            self.pid = None
            self.world_chr_man = None
            self._player = None
            self._boss = None

    def attach(self, relaunch=True, timeout=30.0, poll=1.0):
        t0 = time.time()
        launched = False
        last_err = None

        while time.time() - t0 < timeout:
            try:
                pid = self._current_ds3_pid()
                if pid is None:
                    raise RuntimeError("DS3 not running yet")

                # If process restarted, ensure we don't keep old handles
                if self.pid is not None and pid != self.pid:
                    self._detach()

                self.ds3 = pymem.Pymem("DarkSoulsIII.exe")
                self.pid = pid
                self.module = pymem.process.module_from_name(self.ds3.process_handle, "DarkSoulsIII.exe")

                # probe read
                _ = self.ds3.read_int(self.module.lpBaseOfDll)
                return launched

            except Exception as e:
                last_err = e
                self._detach()

                if relaunch and not launched:
                    # IMPORTANT: call your enter_game correctly (see section 4)
                    import ds3_open as open
                    ok = open.enter_game(timeout=90.0)
                    if not ok:
                        raise RuntimeError("Failed to start DS3 process via launcher")
                    launched = True

                time.sleep(poll)

        raise RuntimeError(f"Could not attach within {timeout}s. Last error: {last_err}")

    def ensure_attached(self):
        # if not attached or PID changed -> attach
        pid = self._current_ds3_pid()
        if self.ds3 is None or self.module is None or self.pid is None or pid != self.pid:
            self.attach(relaunch=True)
            return

        # probe read; any failure -> detach + attach
        try:
            _ = self.ds3.read_int(self.module.lpBaseOfDll)
        except Exception:
            self._detach()
            self.attach(relaunch=True)

    def refresh(self):
        self.ensure_attached()
        self.world_chr_man = self._get_world_chr_man()
        self._player = self._create_player()
        self._boss = self._create_boss(self.enemy)

    def initialize(self):
        self.refresh()

    @property 
    def player(self):
        return self._player


    @property 
    def boss(self):
        return self._boss


    def _create_boss(self, boss):
        return Entity(self._get_entity(boss), self)


    def _create_player(self):
        player_addr = self.follow_chain(self.world_chr_man, [0x80, 0x1F90])
        return Entity(player_addr, self)


    def _get_entity(self, entity_identifier):
        """
        Currently checks using entity Max HP. 
        Ideally would use NPCParam (ID), but can't figure out the offsets.
        """

        chr_num = self.ds3.read_int(self.ds3.read_longlong(self.world_chr_man + 0x1D0))
        chr_set = self.follow_chain(self.world_chr_man, [0x1D0, 0x8])
        
        entity = None
        for i in range(chr_num):
            chr_data = self.follow_chain(chr_set, [i * 0x38, 0x1F90])
            sprj_chr_data_module = self.follow_chain(chr_data, [0x18])
            if self.ds3.read_int(sprj_chr_data_module + 0xDC) == entity_identifier:
                entity = chr_data
        
        if entity is None: 
            raise ValueError(f'Entity with identifier [{entity_identifier}] could not be found.')

        return entity


    def _get_world_chr_man(self): 
        instr = pymem.pattern.pattern_scan_module(
            self.ds3.process_handle,
            self.module,
            WORLD_CHR_MAN_PATTERN,
            return_multiple=False
        )
        offset = self.ds3.read_int(instr + 3)
        world_chr_man_addr = instr + 7 + offset

        return self.ds3.read_longlong(world_chr_man_addr)


    def follow_chain(self, addr, offsets):
        """
        Follows a pointer chain given a list of offsets.
        Ex: *(*(*(addr + offset1) + offset2) + ...) where * is dereferencing.
        """

        ptr = addr
        for offset in offsets:
            try:
                ptr = self.ds3.read_longlong(ptr + offset)

                if self.debug:
                    print(hex(ptr))

            except Exception as e:
                if self.debug:
                    print("Error handling memory offsets. Most likely harmless but a pointer chain did fail.")
                    print(e)

        return ptr
