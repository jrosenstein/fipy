import sys
from fipy.tools import numerix 

def _optionalInline(inlineFn, pythonFn, *args):
    if '--inline' in sys.argv[1:]:
        return inlineFn(*args)
    else:
        return pythonFn(*args)
                         
def _runInline(code_in, converters=None, verbose=0, **args):
    argsKeys = args.keys()
    dimList = ['i', 'j', 'k']
          
    if 'ni' in argsKeys:
        dimensions = 1
        if 'nj' in argsKeys:
            dimensions = 2
            if 'nk' in argsKeys:
                dimensions = 3
    else:
        dimensions = 0
    
    if dimensions == 0:
        code = """ { %s } """ % code_in 
    else:
        loops = """"""
        enders = """"""
        declarations = []
        for dim in range(dimensions):
            d = dimList[dim]
            declarations.append(d)
            loops += "\t" * dim + "for(%s=0;%s<n%s;%s++) {\n" % (d,d,d,d)
            enders += "\n" + "\t" * (dimensions - dim -1) + "}"
        code = 'int ' + ','.join(declarations) + ';\n' + loops + "\t" * dimensions + code_in + enders

    from scipy import weave

    for key in args.keys():
        if hasattr(args[key], 'dtype') and args[key].dtype.char == '?':
            args[key] = args[key].astype('B')

    weave.inline(code,
                 args.keys(),
                 local_dict=args,
                 type_converters=None, #weave.converters.blitz,
                 compiler = 'gcc',
                 force=0,
                 verbose = 0 or verbose,
                 extra_compile_args =['-O3'])

                 
def _runIterateElementInline(code_in, converters=None, verbose=0, **args):
    loops = """
int i;
for(i=0; i < ni; i++) {

"""

    enders = ""
    
    shape = args['shape']
    rank = len(shape) - 1
    for dim in range(rank):
        loops += "\t" * (dim + 1) + "for (vec[%(dim)d]=0; vec[%(dim)d] < shape[%(dim)d]; vec[%(dim)d]++) {\n" % {'dim': dim}
        enders += "\n" + "\t" * (rank - dim) + "}"
        
    enders += """

}
"""
        
    code = """
    #define ITEM(arr,i,vec) (arr[arrayIndex(arr##_array, i, vec)])
                    
    int vec[%(rank)d];
    %(loops)s%(indent)s%(code)s%(enders)s
                    
    #undef ITEM
    """ % {
        'rank': rank, 
        'loops': loops, 
        'indent': "\t" * rank, 
        'code': code_in, 
        'enders': enders
    }

    from scipy import weave

    for key in args.keys():
        if hasattr(args[key], 'dtype') and args[key].dtype.char == '?':
            args[key] = args[key].astype('B')
            
    weave.inline(code,
                 args.keys(),
                 local_dict=args,
                 type_converters=None, #weave.converters.blitz,
                 compiler = 'gcc',
                 force=0,
                 verbose = 0 or verbose,
                 extra_compile_args =['-O3'],
                 support_code="""
                 
// returns the index (accounting for strides) of the tensor element vec 
// in position i of array
//
// array holds a tensor at each position i
// vec identifies a particular element in that tensor
static int arrayIndex(PyArrayObject* array, int i, int vec[])
{
    int index = array->strides[array->nd-1] * i;
    
    if (vec != NULL) {
        int j;
        for (j=0; j < array->nd - 1; j++) {
            index += array->strides[j] * vec[j];
        }
    }
    
    return index / array->descr->elsize;
}
                 """)

