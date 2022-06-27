#!/bin/bash

set -e

python3 -c "import unified_planning.engines"
python3 -c "import unified_planning.engines.compilers"
python3 -c "import unified_planning.engines.mixins"
python3 -c "import unified_planning.grpc"
python3 -c "import unified_planning.interop"
python3 -c "import unified_planning.io"
python3 -c "import unified_planning.model"
python3 -c "import unified_planning.model.htn"
python3 -c "import unified_planning.model.mixins"
python3 -c "import unified_planning.model.walkers"
python3 -c "import unified_planning.plans"
