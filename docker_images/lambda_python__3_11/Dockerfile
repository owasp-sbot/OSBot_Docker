FROM public.ecr.aws/lambda/python:3.11

# Copy the function loader
COPY handler.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD ["handler.run"]