/*
 * system.h - SOPC Builder system and BSP software package information
 *
 * Machine generated for CPU 'nios2_gen2_0' in SOPC Builder design 'soc_system'
 * SOPC Builder design path: ../../soc_system.sopcinfo
 *
 * Generated: Tue Aug 21 10:55:47 CDT 2018
 */

/*
 * DO NOT MODIFY THIS FILE
 *
 * Changing this file will have subtle consequences
 * which will almost certainly lead to a nonfunctioning
 * system. If you do modify this file, be aware that your
 * changes will be overwritten and lost when this file
 * is generated again.
 *
 * DO NOT MODIFY THIS FILE
 */

/*
 * License Agreement
 *
 * Copyright (c) 2008
 * Altera Corporation, San Jose, California, USA.
 * All rights reserved.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 *
 * This agreement shall be governed in all respects by the laws of the State
 * of California and by the laws of the United States of America.
 */

#ifndef __SYSTEM_H_
#define __SYSTEM_H_

/* Include definitions from linker script generator */
#include "linker.h"


/*
 * CPU configuration
 *
 */

#define ALT_CPU_ARCHITECTURE "altera_nios2_gen2"
#define ALT_CPU_BIG_ENDIAN 0
#define ALT_CPU_BREAK_ADDR 0x00000820
#define ALT_CPU_CPU_ARCH_NIOS2_R1
#define ALT_CPU_CPU_FREQ 50000000u
#define ALT_CPU_CPU_ID_SIZE 22
#define ALT_CPU_CPU_ID_VALUE 0x00300005
#define ALT_CPU_CPU_IMPLEMENTATION "tiny"
#define ALT_CPU_DATA_ADDR_WIDTH 0x12
#define ALT_CPU_DCACHE_LINE_SIZE 0
#define ALT_CPU_DCACHE_LINE_SIZE_LOG2 0
#define ALT_CPU_DCACHE_SIZE 0
#define ALT_CPU_EXCEPTION_ADDR 0x00010020
#define ALT_CPU_FLASH_ACCELERATOR_LINES 0
#define ALT_CPU_FLASH_ACCELERATOR_LINE_SIZE 0
#define ALT_CPU_FLUSHDA_SUPPORTED
#define ALT_CPU_FREQ 50000000
#define ALT_CPU_HARDWARE_DIVIDE_PRESENT 0
#define ALT_CPU_HARDWARE_MULTIPLY_PRESENT 0
#define ALT_CPU_HARDWARE_MULX_PRESENT 0
#define ALT_CPU_HAS_DEBUG_CORE 1
#define ALT_CPU_HAS_DEBUG_STUB
#define ALT_CPU_HAS_ILLEGAL_INSTRUCTION_EXCEPTION
#define ALT_CPU_HAS_JMPI_INSTRUCTION
#define ALT_CPU_ICACHE_LINE_SIZE 0
#define ALT_CPU_ICACHE_LINE_SIZE_LOG2 0
#define ALT_CPU_ICACHE_SIZE 0
#define ALT_CPU_INST_ADDR_WIDTH 0x11
#define ALT_CPU_NAME "nios2_gen2_0"
#define ALT_CPU_OCI_VERSION 1
#define ALT_CPU_RESET_ADDR 0x00010000


/*
 * CPU configuration (with legacy prefix - don't use these anymore)
 *
 */

#define NIOS2_BIG_ENDIAN 0
#define NIOS2_BREAK_ADDR 0x00000820
#define NIOS2_CPU_ARCH_NIOS2_R1
#define NIOS2_CPU_FREQ 50000000u
#define NIOS2_CPU_ID_SIZE 22
#define NIOS2_CPU_ID_VALUE 0x00300005
#define NIOS2_CPU_IMPLEMENTATION "tiny"
#define NIOS2_DATA_ADDR_WIDTH 0x12
#define NIOS2_DCACHE_LINE_SIZE 0
#define NIOS2_DCACHE_LINE_SIZE_LOG2 0
#define NIOS2_DCACHE_SIZE 0
#define NIOS2_EXCEPTION_ADDR 0x00010020
#define NIOS2_FLASH_ACCELERATOR_LINES 0
#define NIOS2_FLASH_ACCELERATOR_LINE_SIZE 0
#define NIOS2_FLUSHDA_SUPPORTED
#define NIOS2_HARDWARE_DIVIDE_PRESENT 0
#define NIOS2_HARDWARE_MULTIPLY_PRESENT 0
#define NIOS2_HARDWARE_MULX_PRESENT 0
#define NIOS2_HAS_DEBUG_CORE 1
#define NIOS2_HAS_DEBUG_STUB
#define NIOS2_HAS_ILLEGAL_INSTRUCTION_EXCEPTION
#define NIOS2_HAS_JMPI_INSTRUCTION
#define NIOS2_ICACHE_LINE_SIZE 0
#define NIOS2_ICACHE_LINE_SIZE_LOG2 0
#define NIOS2_ICACHE_SIZE 0
#define NIOS2_INST_ADDR_WIDTH 0x11
#define NIOS2_OCI_VERSION 1
#define NIOS2_RESET_ADDR 0x00010000


/*
 * Define for each module class mastered by the CPU
 *
 */

#define __ALTERA_AVALON_DMA
#define __ALTERA_AVALON_JTAG_UART
#define __ALTERA_AVALON_ONCHIP_MEMORY2
#define __ALTERA_AVALON_PIO
#define __ALTERA_AVALON_SYSID_QSYS
#define __ALTERA_AVALON_TIMER
#define __ALTERA_NIOS2_GEN2


/*
 * System configuration
 *
 */

#define ALT_DEVICE_FAMILY "Cyclone V"
#define ALT_ENHANCED_INTERRUPT_API_PRESENT
#define ALT_IRQ_BASE NULL
#define ALT_LOG_PORT "/dev/null"
#define ALT_LOG_PORT_BASE 0x0
#define ALT_LOG_PORT_DEV null
#define ALT_LOG_PORT_TYPE ""
#define ALT_NUM_EXTERNAL_INTERRUPT_CONTROLLERS 0
#define ALT_NUM_INTERNAL_INTERRUPT_CONTROLLERS 1
#define ALT_NUM_INTERRUPT_CONTROLLERS 1
#define ALT_STDERR "/dev/nios_comms"
#define ALT_STDERR_BASE 0x23000
#define ALT_STDERR_DEV nios_comms
#define ALT_STDERR_IS_JTAG_UART
#define ALT_STDERR_PRESENT
#define ALT_STDERR_TYPE "altera_avalon_jtag_uart"
#define ALT_STDIN "/dev/nios_comms"
#define ALT_STDIN_BASE 0x23000
#define ALT_STDIN_DEV nios_comms
#define ALT_STDIN_IS_JTAG_UART
#define ALT_STDIN_PRESENT
#define ALT_STDIN_TYPE "altera_avalon_jtag_uart"
#define ALT_STDOUT "/dev/nios_comms"
#define ALT_STDOUT_BASE 0x23000
#define ALT_STDOUT_DEV nios_comms
#define ALT_STDOUT_IS_JTAG_UART
#define ALT_STDOUT_PRESENT
#define ALT_STDOUT_TYPE "altera_avalon_jtag_uart"
#define ALT_SYSTEM_NAME "soc_system"


/*
 * hal configuration
 *
 */

#define ALT_MAX_FD 4
#define ALT_SYS_CLK none
#define ALT_TIMESTAMP_CLK NIOS_PERFTIMER


/*
 * hps_0_bridges configuration as viewed by lb_dma_write_master
 *
 */

#define LB_DMA_WRITE_MASTER_HPS_0_BRIDGES_BASE 0x0
#define LB_DMA_WRITE_MASTER_HPS_0_BRIDGES_IRQ -1
#define LB_DMA_WRITE_MASTER_HPS_0_BRIDGES_IRQ_INTERRUPT_CONTROLLER_ID -1
#define LB_DMA_WRITE_MASTER_HPS_0_BRIDGES_NAME "/dev/hps_0_bridges"
#define LB_DMA_WRITE_MASTER_HPS_0_BRIDGES_SPAN 4294967296
#define LB_DMA_WRITE_MASTER_HPS_0_BRIDGES_TYPE "hps_bridge_avalon"


/*
 * lb_dma configuration
 *
 */

#define ALT_MODULE_CLASS_lb_dma altera_avalon_dma
#define LB_DMA_ALLOW_BYTE_TRANSACTIONS 0
#define LB_DMA_ALLOW_DOUBLEWORD_TRANSACTIONS 0
#define LB_DMA_ALLOW_HW_TRANSACTIONS 0
#define LB_DMA_ALLOW_QUADWORD_TRANSACTIONS 0
#define LB_DMA_ALLOW_WORD_TRANSACTIONS 1
#define LB_DMA_BASE 0x22000
#define LB_DMA_IRQ 0
#define LB_DMA_IRQ_INTERRUPT_CONTROLLER_ID 0
#define LB_DMA_LENGTHWIDTH 9
#define LB_DMA_MAX_BURST_SIZE 64
#define LB_DMA_NAME "/dev/lb_dma"
#define LB_DMA_SPAN 32
#define LB_DMA_TYPE "altera_avalon_dma"


/*
 * linebuf configuration as viewed by lb_dma_read_master
 *
 */

#define LB_DMA_READ_MASTER_LINEBUF_ALLOW_IN_SYSTEM_MEMORY_CONTENT_EDITOR 0
#define LB_DMA_READ_MASTER_LINEBUF_ALLOW_MRAM_SIM_CONTENTS_ONLY_FILE 0
#define LB_DMA_READ_MASTER_LINEBUF_BASE 0x0
#define LB_DMA_READ_MASTER_LINEBUF_CONTENTS_INFO ""
#define LB_DMA_READ_MASTER_LINEBUF_DUAL_PORT 1
#define LB_DMA_READ_MASTER_LINEBUF_GUI_RAM_BLOCK_TYPE "M10K"
#define LB_DMA_READ_MASTER_LINEBUF_INIT_CONTENTS_FILE "soc_system_linebuf"
#define LB_DMA_READ_MASTER_LINEBUF_INIT_MEM_CONTENT 0
#define LB_DMA_READ_MASTER_LINEBUF_INSTANCE_ID "NONE"
#define LB_DMA_READ_MASTER_LINEBUF_IRQ -1
#define LB_DMA_READ_MASTER_LINEBUF_IRQ_INTERRUPT_CONTROLLER_ID -1
#define LB_DMA_READ_MASTER_LINEBUF_NAME "/dev/linebuf"
#define LB_DMA_READ_MASTER_LINEBUF_NON_DEFAULT_INIT_FILE_ENABLED 0
#define LB_DMA_READ_MASTER_LINEBUF_RAM_BLOCK_TYPE "M10K"
#define LB_DMA_READ_MASTER_LINEBUF_READ_DURING_WRITE_MODE "DONT_CARE"
#define LB_DMA_READ_MASTER_LINEBUF_SINGLE_CLOCK_OP 1
#define LB_DMA_READ_MASTER_LINEBUF_SIZE_MULTIPLE 1
#define LB_DMA_READ_MASTER_LINEBUF_SIZE_VALUE 1024
#define LB_DMA_READ_MASTER_LINEBUF_SPAN 1024
#define LB_DMA_READ_MASTER_LINEBUF_TYPE "altera_avalon_onchip_memory2"
#define LB_DMA_READ_MASTER_LINEBUF_WRITABLE 1


/*
 * lr_status configuration
 *
 */

#define ALT_MODULE_CLASS_lr_status altera_avalon_pio
#define LR_STATUS_BASE 0x20000
#define LR_STATUS_BIT_CLEARING_EDGE_REGISTER 0
#define LR_STATUS_BIT_MODIFYING_OUTPUT_REGISTER 0
#define LR_STATUS_CAPTURE 0
#define LR_STATUS_DATA_WIDTH 3
#define LR_STATUS_DO_TEST_BENCH_WIRING 0
#define LR_STATUS_DRIVEN_SIM_VALUE 0
#define LR_STATUS_EDGE_TYPE "NONE"
#define LR_STATUS_FREQ 50000000
#define LR_STATUS_HAS_IN 1
#define LR_STATUS_HAS_OUT 0
#define LR_STATUS_HAS_TRI 0
#define LR_STATUS_IRQ -1
#define LR_STATUS_IRQ_INTERRUPT_CONTROLLER_ID -1
#define LR_STATUS_IRQ_TYPE "NONE"
#define LR_STATUS_NAME "/dev/lr_status"
#define LR_STATUS_RESET_VALUE 0
#define LR_STATUS_SPAN 16
#define LR_STATUS_TYPE "altera_avalon_pio"


/*
 * nios_comms configuration
 *
 */

#define ALT_MODULE_CLASS_nios_comms altera_avalon_jtag_uart
#define NIOS_COMMS_BASE 0x23000
#define NIOS_COMMS_IRQ 1
#define NIOS_COMMS_IRQ_INTERRUPT_CONTROLLER_ID 0
#define NIOS_COMMS_NAME "/dev/nios_comms"
#define NIOS_COMMS_READ_DEPTH 64
#define NIOS_COMMS_READ_THRESHOLD 8
#define NIOS_COMMS_SPAN 8
#define NIOS_COMMS_TYPE "altera_avalon_jtag_uart"
#define NIOS_COMMS_WRITE_DEPTH 64
#define NIOS_COMMS_WRITE_THRESHOLD 8


/*
 * nios_perftimer configuration
 *
 */

#define ALT_MODULE_CLASS_nios_perftimer altera_avalon_timer
#define NIOS_PERFTIMER_ALWAYS_RUN 1
#define NIOS_PERFTIMER_BASE 0x24000
#define NIOS_PERFTIMER_COUNTER_SIZE 32
#define NIOS_PERFTIMER_FIXED_PERIOD 1
#define NIOS_PERFTIMER_FREQ 50000000
#define NIOS_PERFTIMER_IRQ 2
#define NIOS_PERFTIMER_IRQ_INTERRUPT_CONTROLLER_ID 0
#define NIOS_PERFTIMER_LOAD_VALUE -2
#define NIOS_PERFTIMER_MULT 2.0E-8
#define NIOS_PERFTIMER_NAME "/dev/nios_perftimer"
#define NIOS_PERFTIMER_PERIOD -1
#define NIOS_PERFTIMER_PERIOD_UNITS "clocks"
#define NIOS_PERFTIMER_RESET_OUTPUT 0
#define NIOS_PERFTIMER_SNAPSHOT 1
#define NIOS_PERFTIMER_SPAN 32
#define NIOS_PERFTIMER_TICKS_PER_SEC 0
#define NIOS_PERFTIMER_TIMEOUT_PULSE_OUTPUT 0
#define NIOS_PERFTIMER_TYPE "altera_avalon_timer"


/*
 * nios_program configuration
 *
 */

#define ALT_MODULE_CLASS_nios_program altera_avalon_onchip_memory2
#define NIOS_PROGRAM_ALLOW_IN_SYSTEM_MEMORY_CONTENT_EDITOR 0
#define NIOS_PROGRAM_ALLOW_MRAM_SIM_CONTENTS_ONLY_FILE 0
#define NIOS_PROGRAM_BASE 0x10000
#define NIOS_PROGRAM_CONTENTS_INFO ""
#define NIOS_PROGRAM_DUAL_PORT 1
#define NIOS_PROGRAM_GUI_RAM_BLOCK_TYPE "AUTO"
#define NIOS_PROGRAM_INIT_CONTENTS_FILE "soc_system_nios_program"
#define NIOS_PROGRAM_INIT_MEM_CONTENT 1
#define NIOS_PROGRAM_INSTANCE_ID "NONE"
#define NIOS_PROGRAM_IRQ -1
#define NIOS_PROGRAM_IRQ_INTERRUPT_CONTROLLER_ID -1
#define NIOS_PROGRAM_NAME "/dev/nios_program"
#define NIOS_PROGRAM_NON_DEFAULT_INIT_FILE_ENABLED 0
#define NIOS_PROGRAM_RAM_BLOCK_TYPE "AUTO"
#define NIOS_PROGRAM_READ_DURING_WRITE_MODE "DONT_CARE"
#define NIOS_PROGRAM_SINGLE_CLOCK_OP 1
#define NIOS_PROGRAM_SIZE_MULTIPLE 1
#define NIOS_PROGRAM_SIZE_VALUE 16384
#define NIOS_PROGRAM_SPAN 16384
#define NIOS_PROGRAM_TYPE "altera_avalon_onchip_memory2"
#define NIOS_PROGRAM_WRITABLE 1


/*
 * sysid_qsys configuration
 *
 */

#define ALT_MODULE_CLASS_sysid_qsys altera_avalon_sysid_qsys
#define SYSID_QSYS_BASE 0x21000
#define SYSID_QSYS_ID -1395049680
#define SYSID_QSYS_IRQ -1
#define SYSID_QSYS_IRQ_INTERRUPT_CONTROLLER_ID -1
#define SYSID_QSYS_NAME "/dev/sysid_qsys"
#define SYSID_QSYS_SPAN 8
#define SYSID_QSYS_TIMESTAMP 1534866647
#define SYSID_QSYS_TYPE "altera_avalon_sysid_qsys"

#endif /* __SYSTEM_H_ */
