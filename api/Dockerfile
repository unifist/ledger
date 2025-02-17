FROM gaf3/python-cryptography-alpine:0.1.0

RUN mkdir -p /opt/service

WORKDIR /opt/service

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
	&& find /usr/local -depth \
		\( \
			\( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
			-o \
			\( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
		\) -exec rm -rf '{}' + \
	&& rm requirements.txt

COPY ddl ddl
COPY bin bin
COPY lib lib

ENV PYTHONPATH "/opt/service/lib:${PYTHONPATH}"

CMD ["/opt/service/bin/api.py"]
