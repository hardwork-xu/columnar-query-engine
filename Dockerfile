FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir .
ENV OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
USER 65534:65534
ENTRYPOINT ["python", "-m", "segmentlens"]
CMD ["demo"]
