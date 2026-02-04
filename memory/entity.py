class Entity: 

    def __init__(self, addr, ds3):
        self._ds3 = ds3
        self._hp_addr = addr + 0xD8
        self._max_hp_addr = addr + 0xDC
        self._sp_addr = addr + 0xF0
        self._max_sp_addr = addr + 0xF4

        self._max_hp = ds3.read_int(self._max_hp_addr) 
        self._max_sp = ds3.read_int(self._max_sp_addr) 


    @property
    def hp():
        return self.ds3.read_int(self._hp_addr)


    @property
    def max_hp():
        return self._max_hp 


    @property
    def sp():
        self.ds3.read_int(self._max_hp_addr)


    @property
    def max_sp():
        return self._max_sp


    @property
    def norm_hp(self):
        return self.hp / self.max_hp


    @property
    def norm_sp(self):
        return self.sp / self.max_sp
