# tb/models/addr_map.py
# Independent address decode reference model based strictly on docs/spec.md Section 5.3
# Address Map:
#   0x4000_0000 - 0x4000_FFFF: Slave 0 (APB Subsystem: UART, Timer, GPIO)
#   0x5000_0000 - 0x5000_FFFF: Slave 1 (1 KB Scratchpad RAM, words 0..255)
#   0x6000_0000 - 0x6000_FFFF: Slave 2 (CSR Block & IRQ Aggregation)
#   0x7000_0000 - 0x7000_FFFF: Slave 3 (CDC Bridge to Slow Regs)
#   All other addresses:       Default Slave (DECERR)

class AddrMap:
    SLAVE_APB = 0
    SLAVE_RAM = 1
    SLAVE_CSR = 2
    SLAVE_CDC = 3
    SLAVE_DECERR = None

    RESP_OKAY   = 0b00
    RESP_EXOKAY = 0b01
    RESP_SLVERR = 0b10
    RESP_DECERR = 0b11

    @staticmethod
    def decode(addr):
        """Decodes a 32-bit physical address into target slave and sub-region.
        Returns: (slave_idx, target_name, is_mapped)
        """
        addr = addr & 0xFFFF_FFFF
        base = addr & 0xF000_0000
        offset = addr & 0x0FFF_FFFF

        if base == 0x4000_0000:
            # S0: APB Subsystem
            apb_target = (offset >> 12) & 0xF
            if apb_target == 0:
                return (AddrMap.SLAVE_APB, "UART", True)
            elif apb_target == 1:
                return (AddrMap.SLAVE_APB, "TIMER", True)
            elif apb_target == 2:
                return (AddrMap.SLAVE_APB, "GPIO", True)
            else:
                return (AddrMap.SLAVE_APB, "APB_UNMAPPED", False)

        elif base == 0x5000_0000:
            # S1: RAM Subsystem (1 KB = 256 32-bit words, 0x000 to 0x3FC)
            if offset < 0x400:
                return (AddrMap.SLAVE_RAM, "RAM", True)
            else:
                return (AddrMap.SLAVE_RAM, "RAM_OUT_OF_BOUNDS", False)

        elif base == 0x6000_0000:
            # S2: CSR Block (0x00 to 0x20 mapped)
            if offset <= 0x20 and (offset % 4 == 0):
                return (AddrMap.SLAVE_CSR, "CSR", True)
            else:
                return (AddrMap.SLAVE_CSR, "CSR_UNMAPPED", False)

        elif base == 0x7000_0000:
            # S3: CDC Bridge (0x00 to 0x0C mapped)
            if offset <= 0x0C and (offset % 4 == 0):
                return (AddrMap.SLAVE_CDC, "CDC", True)
            else:
                return (AddrMap.SLAVE_CDC, "CDC_UNMAPPED", False)

        else:
            # Unmapped Address Space -> Default Slave
            return (AddrMap.SLAVE_DECERR, "DEFAULT_SLAVE", False)
