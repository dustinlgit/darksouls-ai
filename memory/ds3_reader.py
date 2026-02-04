from .utils import WORLD_CHR_MAN_PATTERN
from .entity import Entity

import pymem


class DS3Reader:

    ds3 = pymem.Pymem("DarkSoulsIII.exe");
    module = pymem.process.module_from_name(ds3.process_handle, "DarkSoulsIII.exe")


    def __init__(self, enemy, debug=False):
        self.debug = debug
        self.enemy = enemy
    

    def initialize(self):
        self.world_chr_man = self._get_world_chr_man()
        self._player = self._create_player()
        self._boss = self._create_boss(self.enemy)
    

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
        return Entity(player_addr, self);


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
                print("Error handling memory offsets. Most likely harmless but a pointer chain did fail.")

                if self.debug:
                    print(e)

        return ptr
