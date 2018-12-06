module cambus (
	// this module is responsible for retiming the camera bus
	// to the 50MHz clock, as well as generating blanking signals
	input logic clk,
	input logic rst,
	
	// the camera bus itself
	input logic cam_clk,
	input logic [11:0] cam_pixel,
	input logic cam_hsync,
	input logic cam_vsync,
	
	// output data
	output logic [11:0] vid_pixel,
	output logic vid_pixsync,
	output logic vid_hblank,
	output logic vid_vblank,
	
	input logic show_test_pattern
);

    // cam_ signals are synchronous to the camera clock
    // vid_ signals are synchronous to the main 50MHz clock
    // _syncN signals are used to synchronize the two

    logic cam_rst; // the reset signal retimed to the camera clock
    logic cam_rst_sync1, cam_rst_sync2, cam_rst_sync3;
    always @(posedge cam_clk) begin
        cam_rst <= cam_rst_sync3;
        cam_rst_sync3 <= cam_rst_sync2;
        cam_rst_sync2 <= cam_rst_sync1;
        cam_rst_sync1 <= rst === 1'b1 ? 1'b1 : 1'b0;
    end
    
    // buffer the cambus input because we have no idea
    // what the setup and hold and etc is
    // also this makes modelsim happier when simulating from VCD
    logic cam_hsync_buf, cam_vsync_buf;
    logic [11:0] cam_pixel_buf;
    always @(posedge cam_clk) begin
        cam_hsync_buf <= cam_hsync;
        cam_vsync_buf <= cam_vsync;
        cam_pixel_buf <= cam_pixel;
    end
	
    // count out pixels and lines so we can make blanking signals
    logic [8:0] pixels, lines;
    logic last_hsync, last_vsync;
    always @(posedge cam_clk) begin
        last_hsync <= cam_hsync_buf;
        // on rising edge of hsync, line has begun
        if ((last_hsync == 1'b0) && (cam_hsync_buf == 1'b1)) begin
            pixels <= 9'd0;
            lines <= lines + 9'd1;
        end else begin
            pixels <= pixels + 9'd1;
        end
        
        last_vsync <= cam_vsync_buf;
        // on rising edge of vsync, frame has begun
        if ((last_vsync == 1'b0) && (cam_vsync_buf == 1'b1)) begin
            lines <= 9'd0;
        end
        
        if (cam_rst) begin
            last_hsync <= 1'b0;
            last_vsync <= 1'b0;
            pixels <= 9'd0;
            lines <= 9'd0;
        end
    end
	
	logic h_visible, v_visible;
    logic [11:0] cam_pixel_out;
	assign h_visible = (pixels < 9'd320);
	assign v_visible = (lines >= 9'd1 && lines < 9'd257);
    logic was_visible;
    always @(posedge cam_clk) begin
        was_visible <= (h_visible && v_visible);
    end
	assign cam_pixel_out = was_visible ? cam_pixel_buf : 12'b0;
    
    // use FIFO to push everything into the vid domain
    logic fifo_rdempty, fifo_rdreq;
    logic [13:0] fifo_out;
    cambus_fifo fifo(
        //     cam_hblank  cam_vblank
        .data({!h_visible, !v_visible, cam_pixel_out}),
        .wrclk(cam_clk),
        .wrreq(!cam_rst),
        
        .q(fifo_out),
        .rdclk(clk),
        .rdreq(fifo_rdreq),
        .rdempty(fifo_rdempty)
    );
    
    // automatically read pixels as they become ready
    assign fifo_rdreq = !fifo_rdempty;
    always @(posedge clk) begin
        // pixel is ready the cycle after fifo_rdreq is asserted
        vid_pixsync <= fifo_rdreq;
    end
    // and hook up all the vid_ side data
    assign {vid_hblank, vid_vblank, vid_pixel} = fifo_out;

endmodule


