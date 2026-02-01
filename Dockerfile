# Use the stable, lightweight Python base image
FROM python:3.12-slim

# Set the working directory (best practice)
WORKDIR /dementia

# Copy the dependency list first
COPY requirements.txt requirements.txt

# Install dependencies. This now succeeds because psycopg2-binary is used.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code 
COPY . /dementia

# Ensure the startup script is executable
RUN chmod a+x boot.sh

# Expose port 5000 for Flask
EXPOSE 5000

# The entry point for the application runner
ENTRYPOINT ["./boot.sh"]