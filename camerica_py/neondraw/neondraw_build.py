from cffi import FFI
ffibuilder = FFI()

ffibuilder.cdef("""
    int nd_testadd1(int v);
    
    void nd_conv_merlin(unsigned int src, unsigned int dst, unsigned int offset, unsigned int gain);
""")

ffibuilder.set_source("neondraw", """
    int nd_testadd1(int v);
    void nd_conv_merlin(unsigned int src, unsigned int dst, unsigned int offset, unsigned int gain);
""", extra_objects=["neondraw.s"])

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)