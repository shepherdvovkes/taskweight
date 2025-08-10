FROM postgres:15-alpine

# Install additional packages
RUN apk add --no-cache \
    postgresql-contrib \
    postgresql-dev \
    gcc \
    musl-dev \
    make \
    python3 \
    py3-pip

# Install Python packages for extensions
RUN pip3 install --no-cache-dir \
    psycopg2-binary \
    python-dateutil

# Copy custom configuration
COPY conf/postgresql.conf /etc/postgresql/postgresql.conf
COPY conf/pg_hba.conf /etc/postgresql/pg_hba.conf

# Set proper permissions
RUN chown postgres:postgres /etc/postgresql/postgresql.conf /etc/postgresql/pg_hba.conf

# Expose port
EXPOSE 5432

# Use custom configuration
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
