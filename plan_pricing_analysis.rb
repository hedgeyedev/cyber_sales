# plan_pricing_analysis.rb -- READ-ONLY. Run via: bin/rails runner /tmp/plan_pricing_analysis.rb
# Lists plan pricings started on/after SINCE (default 2026-10-20) plus any with CY26/cyber in sku or promo_code.
require 'json'
since = Time.zone.parse(ENV.fetch('SINCE', '2026-10-20'))
cols = %i[id sku promo_code category offer_type interval price start_date end_date created_at]
rows = PlanPricing.where("start_date >= ? OR LOWER(sku) LIKE '%cy26%' OR LOWER(promo_code) LIKE '%cy26%' OR LOWER(sku) LIKE '%cyber%' OR LOWER(promo_code) LIKE '%cyber%'", since)
                  .map { |pp| cols.to_h { |c| [c, pp.public_send(c)] } }
File.write('/tmp/plan_pricings.json', JSON.pretty_generate(rows))
puts "plan pricings: #{rows.size}"
