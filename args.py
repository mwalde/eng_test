import sys
# arg test comment

def argtest( **kargs ):
    for key, value in kargs.iteritems():
        print "key = %s, value = %s" % (key,value)



if __name__ == '__main__':
#    print str(sys.argv)
    print str(sys.argv[1:])
#    args =  for arg in sys.argv[1:]])
#    print "args dict ", args
    argtest( str(sys.argv[1:]))
