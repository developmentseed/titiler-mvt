FROM lambci/lambda:build-python3.8

RUN pip install cython==0.28

WORKDIR /tmp

COPY setup.py setup.py
COPY titiler_mvt/ titiler_mvt/

# Install dependencies
RUN pip install . -t /var/task  --no-binary numpy,pydantic

# Leave module precompiles for faster Lambda startup
RUN cd /var/task && find . -type f -name '*.pyc' | while read f; do n=$(echo $f | sed 's/__pycache__\///' | sed 's/.cpython-[2-3][0-9]//'); cp $f $n; done;
RUN cd /var/task && find . -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf
RUN cd /var/task && find . -type f -a -name '*.py' -print0 | xargs -0 rm -f
RUN cd /var/task && find . -type d -a -name 'tests' -print0 | xargs -0 rm -rf
RUN rm -rdf /var/task/numpy/doc/

