FROM python:3.12

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy source code first
COPY . .

# Configure poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --without dev

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Command to run the application
CMD ["poetry", "run", "bot"]