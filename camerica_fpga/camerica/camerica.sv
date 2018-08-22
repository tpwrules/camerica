module camerica (
	// 50MHz main clock
	input logic clk,
	input logic rst,
	
	// camera bus
	
	input logic [11:0] cam_pixel_in,
	input logic cam_hsync_in,
	input logic cam_vsync_in,
	input logic cam_clk_in,

	// Qsys interconnects
	
	// the Qsys video reader
	output logic vi_clk,
	output logic [11:0] vi_data,
	output logic vi_de,
	output logic vi_locked,
	output logic vi_vsync,
	output logic vi_hsync,
	
	// NIOS register access
	output logic nr_acknowledge,
	output logic nr_irq,
	input logic [1:0] nr_address,
	input logic nr_bus_enable,
	input logic nr_rw,
	input logic [31:0] nr_write_data,
	output logic [31:0] nr_read_data,
	
	// HPS register access
	output logic hr_acknowledge,
	output logic hr_irq,
	input logic [1:0] hr_address,
	input logic hr_bus_enable,
	input logic hr_rw,
	input logic [31:0] hr_write_data,
	output logic [31:0] hr_read_data,
	
	// histo mem access
	output logic hm_acknowledge,
	input logic [7:0] hm_address,
	input logic hm_bus_enable,
	input logic hm_rw,
	output logic [63:0] hm_read_data

);

endmodule
