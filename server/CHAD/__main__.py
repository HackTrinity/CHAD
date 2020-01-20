import sys

from . import app

def usage():
    print(f'usage: {sys.argv[0]} <serve|periodic>', file=sys.stderr)
    sys.exit(1)

if len(sys.argv) != 2:
    usage()

if sys.argv[1] == 'cleanup':
    app.cleanup.run()
elif sys.argv[1] == 'serve':
    app.run(debug=True, host='0.0.0.0', port=80)
else:
    usage()
