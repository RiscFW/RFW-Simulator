class Memory:
    def init(self, offset, data):
        self.memory = [0] * 65536

    def dump(self, offset, length):
        pass

    def load(self, offset, size):
        return self.memory[offset] & ((1 << (size + 1)) - 1)

    def store(self, offset, size, data):
        self.memory[offset] = data & ((1 << (size + 1)) - 1)

memory = Memory()

def fetch(i, h, l):
    return (i >> l) & ((1 << (1 + h - l)) - 1)

class CPU:
    def __init__(self):
        self.pc = 0
        self.regs = [0] * 32

    def setPC(self, pc):
        self.pc = pc

    def decode(self, inst):
        res = {}
        
        R_TYPE = 0b0110011
        I_TYPE = 0b0010011
        LOAD   = 0b0000011
        S_TYPE = 0b0100011
        B_TYPE = 0b1100011
        JAL    = 0b1101111
        JALR   = 0b1100111
        
        if (fetch(inst, 6, 0) == R_TYPE): # R-inst
            res["operand_0"] = 1
            res["operand_1"] = 1
            res["load_memory"] = 0
            res["store_memory"] = 0
            res["mem_width"] = 0
            res["write_back"] = 1
            res["jump"] = 0
            res["alu_operation"] = fetch(inst, 14, 12)
            res["funct7"] = fetch(inst, 31, 25)
            res["imm"] = 0
        elif (fetch(inst, 6, 0) == I_TYPE):
            res["operand_0"] = 1
            res["operand_1"] = 0
            res["load_memory"] = 0
            res["store_memory"] = 0
            res["mem_width"] = 0
            res["write_back"] = 1
            res["jump"] = 0
            res["alu_operation"] = fetch(inst, 14, 12)
            res["funct7"] = 0
            res["imm"] = fetch(inst, 31, 20)
        elif (fetch(inst, 6, 0) == LOAD):
            res["operand_0"] = 1
            res["operand_1"] = 0
            res["load_memory"] = 1
            res["store_memory"] = 0
            res["mem_width"] = 1 << fetch(inst, 14, 12)
            res["write_back"] = 1
            res["jump"] = 0
            res["alu_operation"] = 0
            res["funct7"] = 0
            res["imm"] = fetch(inst, 31, 20)
        elif (fetch(inst, 6, 0) == S_TYPE):
            res["operand_0"] = 1
            res["operand_1"] = 0
            res["load_memory"] = 0
            res["store_memory"] = 1
            res["mem_width"] = 1 << fetch(inst, 14, 12)
            res["write_back"] = 1
            res["jump"] = 0
            res["alu_operation"] = 0
            res["funct7"] = 0
            res["imm"] = fetch(inst, 31, 20)
        elif (fetch(inst, 6, 0) == B_TYPE):
            res["operand_0"] = 1
            res["operand_1"] = 1
            res["load_memory"] = 0
            res["store_memory"] = 0
            res["mem_width"] = 0
            res["write_back"] = 1
            res["jump"] = 2
            res["alu_operation"] = 8 + fetch(inst, 14, 12)
            res["funct7"] = 0
            res["imm"] = fetch(inst, 31, 31) << 11 + fetch(inst, 7, 7) << 10 + fetch(inst, 30, 25) << 4 + fetch(inst, 11, 8)
        elif (fetch(inst, 6, 0) == JAL):
            res["operand_0"] = 1
            res["operand_1"] = 0
            res["load_memory"] = 0
            res["store_memory"] = 0
            res["mem_width"] = 0
            res["write_back"] = 1
            res["jump"] = 1
            res["alu_operation"] = 16
            res["funct7"] = 0
            res["imm"] = fetch(inst, 31, 31) << 19 + fetch(inst, 19, 12) << 11 + fetch(inst, 20, 20) << 10 + fetch(inst, 30, 21)
        elif (fetch(inst, 6, 0) == JALR):
            res["operand_0"] = 1
            res["operand_1"] = 0
            res["load_memory"] = 0
            res["store_memory"] = 0
            res["mem_width"] = 0
            res["write_back"] = 1
            res["jump"] = 1
            res["alu_operation"] = 16
            res["funct7"] = 0
            res["imm"] = fetch(inst, 31, 20)

        return res

    def alu(self, alu_0, alu_1, alu_op, funch7):
        if alu_op == 0 and funch7 == 0:
            return alu_0 + alu_1
        elif alu_op == 0 and funch7 == 0b0100000:
            return alu_0 - alu_1
        elif alu_op == 1 :
            return alu_0 << alu_1
        elif alu_op == 2:
            return 1 if alu_0 < alu_1 else 0
        elif alu_op == 3:
            return 1 if alu_0 & 0xffffffff < alu_1 & 0xffffffff else 0
        elif alu_op == 4:
            return alu_0 ^ alu_1
        elif alu_op == 5 and funch7 == 0:
            return alu_0 >> alu_1
        elif alu_op == 5 and funch7 == 0b0100000:
            return alu_0 & 0xffffffff >> alu_1
        elif alu_op == 6:
            return alu_0 | alu_1
        elif alu_op == 7:
            return alu_0 & alu_1
        elif alu_op == 8:
            return 1 if alu_0 == alu_1 else 0
        elif alu_op == 9:
            return 1 if alu_0 != alu_1 else 0
        elif alu_op == 12:
            return 1 if alu_0 < alu_1 else 0
        elif alu_op == 13:
            return 1 if alu_0 >= alu_1 else 0
        elif alu_op == 14:
            return 1 if alu_0 & 0xffffffff < alu_1 & 0xffffffff else 0
        elif alu_op == 15:
            return 1 if alu_0 & 0xffffffff >= alu_1 & 0xffffffff else 0
        elif alu_op == 16:
            return self.pc + 4

        return 0

    def step(self):
        inst = memory.load(self.pc, 4)
        control_signal_bundle = self.decode(inst)
        alu_0 = self.regs[fetch(inst, 19, 15)]
        alu_1 = self.regs[fetch(inst, 24, 20)] if control_signal_bundle["operand_1"] else control_signal_bundle["imm"]
        alu_res = self.alu(alu_0, alu_1, control_signal_bundle["alu_operation"], control_signal_bundle["funct7"])
        if (control_signal_bundle["load_memory"]):
            mem_res = memory.load(alu_res, control_signal_bundle["mem_width"])
        elif (control_signal_bundle["store_memory"]):
            memory.store(alu_res, control_signal_bundle["mem_width"], self.regs[fetch(inst, 24, 20)])
        wb_data = mem_res if control_signal_bundle["load_memory"] else alu_res
        if (control_signal_bundle["write_back"]):
            self.regs[fetch(inst, 11, 7)] = wb_data

        pc += 4
        if control_signal_bundle["jump"] == 1 or \
          (control_signal_bundle["jump"] == 2 and alu_res == 1):
            pc += control_signal_bundle["imm"]
        # 写完了