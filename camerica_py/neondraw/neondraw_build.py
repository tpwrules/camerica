from cffi import FFI
ffibuilder = FFI()

ffibuilder.cdef("""
    int nd_testadd1(int v);
""")

ffibuilder.set_source("neondraw", """
    int nd_testadd1(int v);
""", extra_objects=["neondraw.s"])

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)