class Entity: 

    def __init__(self, addr, reader):
        self.reader = reader

        stats_addr = reader.follow_chain(addr, [0x18])
        pos_addr = reader.follow_chain(addr, [0x68, 0xA8, 0x40])

        self._hp_addr = stats_addr + 0xD8
        self._max_hp_addr = stats_addr + 0xDC
        self._sp_addr = stats_addr + 0xF0
        self._max_sp_addr = stats_addr + 0xF4

        self._max_hp = reader.ds3.read_int(self._max_hp_addr) 
        self._max_sp = reader.ds3.read_int(self._max_sp_addr) 

        self._x_addr = pos_addr + 0x70
        self._z_addr = pos_addr + 0x74
        self._y_addr = pos_addr + 0x78
        
        self._animation_addr = reader.follow_chain(addr, [0x80]) + 0xC8
        self._animation_str_addr = reader.follow_chain(addr, [0x28]) + 0x898
        self._animation_time_addr = reader.follow_chain(addr, [0x10])


    @property
    def hp(self):
        return self.reader.ds3.read_int(self._hp_addr)


    @property
    def max_hp(self):
        return self._max_hp 


    @property
    def sp(self):
        return self.reader.ds3.read_int(self._sp_addr)


    @property
    def max_sp(self):
        return self._max_sp


    @property
    def norm_hp(self):
        return self.hp / self.max_hp


    @property
    def norm_sp(self):
        return self.sp / self.max_sp


    @property
    def x(self):
        return self.reader.ds3.read_float(self._x_addr)


    @property
    def z(self):
        return self.reader.ds3.read_float(self._z_addr)


    @property
    def y(self):
        return self.reader.ds3.read_float(self._y_addr)


    @property
    def pos(self):
        return (self.x, self.z, self.y)
    

    @property
    def animation(self):
        return self.reader.ds3.read_int(self._animation_addr)

    @property
    def animation_str(self):
        try:
            str = self.reader.ds3.read_bytes(self._animation_str_addr, 20).decode()
            if "SABreak" in str:
                return "SABreak"
            return str
        except Exception:
            return "StringReadError"
    
    @property
    def animation_prog(self):
        curr = self.reader.ds3.read_float(self._animation_time_addr + 0x24)
        max = self.reader.ds3.read_float(self._animation_time_addr + 0x2C)
        return curr / max