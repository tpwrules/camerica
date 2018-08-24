module camerica (
	// 50MHz main clock
	input logic clk,
	input logic rst,
	
	// camera bus
	
	input logic cam_clk,
	input logic [11:0] cam_pixel,
	input logic cam_hsync,
	input logic cam_vsync,

	// Qsys interconnects
	
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
	
	// vid mem access
	output logic vm_acknowledge,
	input logic [7:0] vm_address,
	input logic vm_bus_enable,
	input logic vm_rw,
	output logic [63:0] vm_read_data
);

endmodule
