# recurring_payment_analysis.rb
require 'json'
require 'csv'

class RecurringPaymentAnalyzer
  def initialize(start_date)
    @start_date = start_date
    @payments = []
  end

  def collect_data
    # Calculate end date (end of November + Cyber Week)
    # Cyber Week runs through Friday Dec 5, so extend through Dec 6
    # Extended buffer to allow final reports even after the period ends
    today = Date.today
    if today.month == 12 && today.day <= 9 && today.year == @start_date.year
      end_date = Date.new(@start_date.year, 12, 6) # Include all of Cyber Week (through Dec 5)
      puts "NOTE: Including Cyber Week (through December 5th) in analysis"
    else
      end_date = Date.new(@start_date.year, 12, 1) # Standard: through Nov 30
    end

    puts "Fetching payments from #{@start_date} to #{end_date - 1}..."

    # Fetch payment IDs first (fast query), then fetch full records in chunks
    # This avoids timeout on the initial query
    payment_ids = Payment.where("description LIKE 'Recurring Payment for%' AND created_at >= ? AND created_at < ?", @start_date, end_date)
                         .pluck(:id)

    puts "Found #{payment_ids.size} payment IDs, fetching details..."

    # Process in chunks to avoid memory issues
    payment_ids.each_slice(500) do |id_chunk|
      Payment.where(id: id_chunk).includes(:payment_profile).find_each do |payment|
        payment_data = extract_payment_data(payment)
        @payments << payment_data

        print '.' if @payments.size % 100 == 0
      end
    end

    puts "\nCollected #{@payments.size} payments"
  end

  def extract_payment_data(payment)
    data = {
      id: payment.id,
      amount: payment.amount.to_f,
      created_at: payment.created_at.iso8601,
      date: payment.created_at.to_date.to_s,
      hour: payment.created_at.hour,
      day_of_week: payment.created_at.strftime('%A'),
      description: payment.description,
      status: payment.status,
      user_id: payment.user_id
    }

    # Get SKU info if available
    begin
      if payment.payment_profile&.profile_product_ownerships&.any?
        profile_product_ownership = payment.payment_profile.profile_product_ownerships.first
        plan_pricing = profile_product_ownership.plan_pricing

        # Get target service tier
        if profile_product_ownership.target_service_tier
          data[:target_service_tier_name] = profile_product_ownership.target_service_tier.name
        end

        if plan_pricing
          data[:sku] = plan_pricing.sku
          data[:sku_price] = plan_pricing.price.to_f
          data[:interval] = plan_pricing.interval
          data[:offer_type] = plan_pricing.offer_type
          data[:category] = plan_pricing.category
          data[:promo_code] = plan_pricing.promo_code

          # Categorize payment type
          # Use CYBER_YEAR env var to determine which year is "current"
          cyber_year = ENV.fetch('CYBER_YEAR', '2025')
          sku_lower = plan_pricing.sku.to_s.downcase

          # Through 2025 cyber SKUs were named cyber_YYYY; from 2026 they are named ..._CY26_n
          # (e.g. macro_core_1_CY26_1, elite_pass_MNG-SUBS-CY26_1). Treat CYyy as cyber_20yy.
          cy_year = sku_lower[/(?:^|[_-])cy(\d{2})(?:_|$)/, 1]
          sku_cyber_year = sku_lower[/cyber_(\d{4})/, 1] || (cy_year && "20#{cy_year}")

          if sku_cyber_year == cyber_year.to_s
            data[:payment_category] = "cyber_#{cyber_year}"
            data[:is_cyber] = true
          elsif sku_cyber_year
            data[:payment_category] = 'cyber_old'
            data[:is_cyber] = true
          else
            data[:payment_category] = 'normal'
            data[:is_cyber] = false
          end
        end
      end
    rescue => e
      data[:sku_error] = e.message
    end

    data
  end

  def write_json(filename)
    cyber_year = ENV.fetch('CYBER_YEAR', '2025')
    File.write(filename, JSON.pretty_generate({
      generated_at: Time.now.iso8601,
      start_date: @start_date.to_s,
      cyber_year: cyber_year.to_i,
      total_payments: @payments.size,
      total_revenue: @payments.sum { |p| p[:amount] },
      payments: @payments
    }))
    puts "Wrote JSON to #{filename}"
  end

  def write_csv(filename)
    CSV.open(filename, 'w') do |csv|
      # Header
      csv << [
        'id', 'amount', 'created_at', 'date', 'hour', 'day_of_week',
        'description', 'status', 'user_id',
        'target_service_tier_name', 'sku', 'sku_price', 'interval', 'offer_type', 'category', 'promo_code', 'is_cyber', 'payment_category'
      ]
      
      # Data rows
      @payments.each do |payment|
        csv << [
          payment[:id],
          payment[:amount],
          payment[:created_at],
          payment[:date],
          payment[:hour],
          payment[:day_of_week],
          payment[:description],
          payment[:status],
          payment[:user_id],
          payment[:target_service_tier_name],
          payment[:sku],
          payment[:sku_price],
          payment[:interval],
          payment[:offer_type],
          payment[:category],
          payment[:promo_code],
          payment[:is_cyber],
          payment[:payment_category]
        ]
      end
    end
    puts "Wrote CSV to #{filename}"
  end

  def summary
    cyber_year = ENV.fetch('CYBER_YEAR', '2025')
    puts "\n=== SUMMARY ==="
    puts "Total Payments: #{@payments.size}"
    puts "Total Revenue: $#{@payments.sum { |p| p[:amount] }.round(2)}"
    puts "Date Range: #{@payments.first[:date]} to #{@payments.last[:date]}"

    # Payment category breakdown
    cyber_current_payments = @payments.select { |p| p[:payment_category] == "cyber_#{cyber_year}" }
    cyber_old_payments = @payments.select { |p| p[:payment_category] == 'cyber_old' }
    normal_payments = @payments.select { |p| p[:payment_category] == 'normal' }

    total_revenue = @payments.sum { |p| p[:amount] }

    puts "\n=== PAYMENT CATEGORY BREAKDOWN ==="
    puts "Cyber #{cyber_year} Payments: #{cyber_current_payments.size} (#{(cyber_current_payments.size.to_f / @payments.size * 100).round(1)}%)"
    puts "Cyber #{cyber_year} Revenue: $#{cyber_current_payments.sum { |p| p[:amount] }.round(2)} (#{(cyber_current_payments.sum { |p| p[:amount] } / total_revenue * 100).round(1)}%)"
    puts ""
    puts "Cyber Old Payments: #{cyber_old_payments.size} (#{(cyber_old_payments.size.to_f / @payments.size * 100).round(1)}%)"
    puts "Cyber Old Revenue: $#{cyber_old_payments.sum { |p| p[:amount] }.round(2)} (#{(cyber_old_payments.sum { |p| p[:amount] } / total_revenue * 100).round(1)}%)"
    puts ""
    puts "Normal Payments: #{normal_payments.size} (#{(normal_payments.size.to_f / @payments.size * 100).round(1)}%)"
    puts "Normal Revenue: $#{normal_payments.sum { |p| p[:amount] }.round(2)} (#{(normal_payments.sum { |p| p[:amount] } / total_revenue * 100).round(1)}%)"
    
    # Target Service Tier breakdown
    puts "\n=== TARGET SERVICE TIER BREAKDOWN ==="
    tier_groups = @payments.select { |p| p[:target_service_tier_name] }.group_by { |p| p[:target_service_tier_name] }
    tier_groups.each do |tier, payments|
      count = payments.size
      revenue = payments.sum { |p| p[:amount] }
      puts "#{tier}: #{count} payments, $#{revenue.round(2)}"
    end

    # SKU breakdown (grouped by tier)
    puts "\n=== SKU BREAKDOWN BY TIER ==="
    tier_groups.each do |tier, tier_payments|
      puts "\n#{tier}:"
      sku_groups = tier_payments.select { |p| p[:sku] }.group_by { |p| p[:sku] }
      sku_groups.each do |sku, payments|
        count = payments.size
        revenue = payments.sum { |p| p[:amount] }
        puts "  #{sku}: #{count} payments, $#{revenue.round(2)}"
      end
    end
    
    # Daily breakdown
    puts "\n=== DAILY BREAKDOWN ==="
    daily = @payments.group_by { |p| p[:date] }
    daily.keys.sort.each do |date|
      payments = daily[date]
      puts "#{date}: #{payments.size} payments, $#{payments.sum { |p| p[:amount] }.round(2)}"
    end
  end
end

# Run the analysis
# Use CYBER_YEAR env var to determine the November to analyze
cyber_year = ENV.fetch('CYBER_YEAR', '2025').to_i
start_date = Date.new(cyber_year, 11, 1)

puts "\n=== ANALYZING CYBER NOVEMBER #{cyber_year} ==="

analyzer = RecurringPaymentAnalyzer.new(start_date)
analyzer.collect_data
analyzer.summary

# Write outputs - adjust paths as needed
output_dir = "/tmp"
analyzer.write_json("#{output_dir}/recurring_payments.json")
analyzer.write_csv("#{output_dir}/recurring_payments.csv")

puts "\n=== FILES READY ==="
puts "JSON: #{output_dir}/recurring_payments.json"
puts "CSV: #{output_dir}/recurring_payments.csv"
puts "\nYou can now copy these files and analyze locally!"
