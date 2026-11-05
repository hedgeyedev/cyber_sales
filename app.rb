#!/usr/bin/env ruby
# Minimal Sinatra app to serve Cyber Sales reports
# No database, no sessions, just static HTML serving with basic auth

require 'sinatra'
require 'rack/auth/basic'

# Configuration
set :port, ENV.fetch('PORT', 4567).to_i
set :bind, '0.0.0.0'
set :public_folder, File.dirname(__FILE__)  # In K8s, this will be /app (EFS mount)

# Basic authentication for internal users
use Rack::Auth::Basic, "Cyber Sales Reports" do |username, password|
  # Credentials from environment variables
  # Set these before running:
  #   export REPORTS_USER=your_username
  #   export REPORTS_PASS=your_password
  expected_user = ENV.fetch('REPORTS_USER', 'hedgeye')
  expected_pass = ENV.fetch('REPORTS_PASS', 'change_me_in_production')

  username == expected_user && password == expected_pass
end

# Serve index.html at root
get '/' do
  send_file File.join(settings.public_folder, 'index.html')
end

# Optional: Add a refresh endpoint for manual triggering
# Uncomment if you want web-based refresh capability
# post '/refresh' do
#   # Require admin password for refresh trigger
#   halt 401 unless params[:admin_password] == ENV['ADMIN_PASSWORD']
#
#   # Run refresh script in background
#   system("#{settings.public_folder}/refresh_analysis.sh &")
#
#   "Refresh started! Check back in a few minutes."
# end

# Health check endpoint (no auth required)
get '/health' do
  content_type :json
  { status: 'ok', timestamp: Time.now.iso8601 }.to_json
end

# All other files (.html, .css, .js, etc.) are served automatically
# by Sinatra from the public_folder directory
