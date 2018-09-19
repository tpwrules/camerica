module linereader(
	input logic clk,
	input logic rst,
	
	// video input
	input logic [11:0] vid_pixel,
	input logic vid_pixsync,
	input logic vid_hblank,
	input logic vid_vblank,
	input logic vid_visible,

	// video memory access
	output logic vm_acknowledge,
	input logic [8:0] vm_address,
	input logic vm_bus_enable,
	input logic vm_rw,
	output logic [63:0] vm_read_data,
	
	// status output
	output logic status_which_line,
	output logic status_which_histo
);
	
	// instantiate the two memories
	logic [11:0] lr_data_in;
	logic [7:0] lr_vma_addr;
	logic [9:0] lr_addr;
	logic lr_wren;
	logic [47:0] lr_vma_data_out;
	line_ram line_ram(
		.clock(clk),
		.rdaddress(lr_vma_addr),
		.q(lr_vma_data_out),
		
		.wren(lr_wren),
		.wraddress(lr_addr),
		.data(lr_data_in)
	);
	
	logic hr_wren;
	logic [8:0] hr_addr;
	logic [26:0] hr_data_in;
	logic [26:0] hr_data_out;
	
	logic [7:0] hr_vma_addr;
	logic [53:0] hr_vma_data_out;
	
	histo_ram histo_ram(
		.clock(clk),
		.wren_a(hr_wren),
		.address_a(hr_addr),
		.data_a(hr_data_in),
		.q_a(hr_data_out),
		
		.wren_b(1'b0),
		.address_b(hr_vma_addr),
		.data_b(54'b0),
		.q_b(hr_vma_data_out)
	);
	
	// logic to allow video memory to be read
	assign lr_vma_addr = vm_address[7:0];
	assign hr_vma_addr = vm_address[7:0];
	logic vma_should_read;
	assign vma_should_read = vm_rw && vm_bus_enable;
	logic [63:0] lr_vma_result;
	assign lr_vma_result = 
		{lr_vma_data_out[47:36], 4'b0,
		 lr_vma_data_out[35:24], 4'b0,
		 lr_vma_data_out[23:12], 4'b0,
		 lr_vma_data_out[11:0],  4'b0};
	logic [63:0] hr_vma_result;
	assign hr_vma_result = 
		{5'b0, hr_vma_data_out[53:27],
		 5'b0, hr_vma_data_out[26:0]};
    logic vma_which_mem;
	assign vm_read_data = vma_which_mem ? hr_vma_result : lr_vma_result;
	
    // the reader asserts should_read, then we assert ack next cycle
    // but the reader won't deassert should_read til the third cycle
    // so we have to sense the rising edge of should_read so we don't
    // generate a spurious ack
    // this could be a state machine but eh
    logic vma_just_read;
	always @(posedge clk) begin
		if (!rst) begin
            vma_just_read <= vma_should_read;
			vm_acknowledge <= (vma_should_read && !vma_just_read);
            if (vma_should_read && !vma_just_read) begin
                vma_which_mem <= vm_address[8];
            end
		end else begin
			vm_acknowledge <= 1'b0;
            vma_just_read <= 1'b0;
            vma_which_mem <= 1'b0;
		end
	end
	
	typedef enum logic [1:0] {VF_VBLANK, VF_HBLANK, VF_VISIBLE} vid_fsm_t;
	vid_fsm_t vcstate, vnstate;
	
	logic [8:0] xpos;
	
	logic flip_which_line;
	
	always @(posedge clk) begin
		if (rst) begin
			vcstate <= VF_VBLANK;
			xpos <= 9'd0;
		end else begin
			vcstate <= vnstate;
		end
		
		if (vcstate == VF_VISIBLE) begin
			if (vid_pixsync)
				xpos <= xpos + 1'd1;
		end else begin
			xpos <= 9'd0;
		end
		
		if (flip_which_line) begin
			status_which_line <= !status_which_line;
		end
	end
	
	// set up video writer input
	assign lr_data_in = vid_pixel;
	assign lr_addr = {status_which_line, xpos};
	
	always @(*) begin
		vnstate = vcstate;
		flip_which_line = 1'b0;
		lr_wren = 1'b0;
		if (vid_pixsync) begin
			case (vcstate)
				VF_VISIBLE: begin
					lr_wren = 1'b1;
					if (vid_vblank) begin
						vnstate = VF_VBLANK;
						flip_which_line = 1'b1;
					end else if (vid_hblank) begin
						vnstate = VF_HBLANK;
						flip_which_line = 1'b1;
					end
				end
				
				VF_HBLANK: begin
					if (vid_vblank) begin
						vnstate = VF_VBLANK;
					end else if (!vid_hblank) begin
						vnstate = VF_VISIBLE;
					end
				end
				
				VF_VBLANK: begin
					if (vid_visible) begin
						vnstate = VF_VISIBLE;
					end
				end
			endcase
		end
	end
	
	
	typedef enum logic [2:0] {HF_VBLANK, HF_HBLANK,
		HF_READ, HF_WRITE, HF_CLEAR_HRAM} histo_fsm_t;
	histo_fsm_t hcstate, hnstate;
	
	logic flip_which_histo;
	logic [7:0] hram_clear_addr;
	logic [7:0] histo_curr_pix;
	
	always @(posedge clk) begin
		if (rst) begin
			hcstate <= HF_CLEAR_HRAM;
		end else begin
			hcstate <= hnstate;
		end
		
		if (hcstate == HF_CLEAR_HRAM) begin
			hram_clear_addr <= hram_clear_addr + 1'd1;
		end else begin
			hram_clear_addr <= 8'd0;
		end
		
		if (flip_which_histo) begin
			status_which_histo <= !status_which_histo;
		end
		
		if (vid_pixsync) begin
			histo_curr_pix <= vid_pixel[11:4];
		end
	end
	
	
	assign hr_data_in = (hcstate == HF_CLEAR_HRAM) ? 27'd0 :
		(hr_data_out + 1'd1);
	assign hr_addr[8] = status_which_histo;
	
	always @(*) begin
		hnstate = hcstate;
		flip_which_histo = 1'b0;
		hr_wren = 1'b0;
		hr_addr[7:0] = 8'b0;
		
		case (hcstate)
			HF_READ: begin
				if (vid_pixsync) begin
					if (vid_hblank) begin
						hnstate = HF_HBLANK;
					end else if (vid_vblank) begin
						hnstate = HF_CLEAR_HRAM;
						flip_which_histo = 1'b1;
					end else begin
						hr_addr[7:0] = vid_pixel[11:4];
						hnstate = HF_WRITE;
					end
				end
			end
			
			HF_WRITE: begin
				hr_addr[7:0] = histo_curr_pix;
				hr_wren = 1'b1;
				hnstate = HF_READ;
			end
			
			HF_HBLANK: begin
				if (vid_pixsync) begin
					if (vid_vblank) begin
						hnstate = HF_CLEAR_HRAM;
						flip_which_histo = 1'b1;
					end else if (!vid_hblank) begin
						hnstate = HF_READ;
					end
				end
			end
			
			HF_VBLANK: begin
				if (vid_pixsync && vid_visible) begin
					hnstate = HF_READ;
				end
			end
			
			HF_CLEAR_HRAM: begin
				hr_addr[7:0] = hram_clear_addr;
				hr_wren = 1'b1;
				if (hram_clear_addr == 8'hff) begin
					hnstate = HF_VBLANK;
				end
			end
		endcase
	end
	
endmodule
