# Minimal Docker image for Cyber Sales Reports web server
# IMPORTANT: Must build for x86 to run on AWS EKS
FROM --platform=linux/amd64 ruby:3.2-slim

# Install build dependencies (slim uses apt, not apk)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY Gemfile Gemfile.lock* ./

# Install gems
RUN bundle install --without development test

# Copy application code
COPY . .

# Environment variables (override these when running)
ENV REPORTS_USER=hedgeye
ENV REPORTS_PASS=change_me_in_production
ENV PORT=4567

# Expose port (for documentation, Kubernetes uses containerPort from manifest)
EXPOSE 4567

# Run the application
CMD ["bundle", "exec", "rackup", "--host", "0.0.0.0", "-p", "4567"]
