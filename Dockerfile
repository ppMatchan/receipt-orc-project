FROM public.ecr.aws/lambda/python:3.12

RUN dnf install -y \
    libxcb \
    libX11 \
    libXext \
    libXrender \
    libgomp \
    mesa-libGL \
    && dnf clean all

COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install --no-cache-dir -r requirements.txt

COPY lambda_handler.py ${LAMBDA_TASK_ROOT}
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY config/ ${LAMBDA_TASK_ROOT}/config/

COPY data/discount_keywords.json ${LAMBDA_TASK_ROOT}/data/
COPY data/non_item_keywords.json ${LAMBDA_TASK_ROOT}/data/
COPY data/summary_keywords.json ${LAMBDA_TASK_ROOT}/data/

CMD ["lambda_handler.lambda_handler"]