#!/usr/bin/env ruby
require 'optparse'
require 'yaml'

def is_f?(s)
  !!Float(s)
rescue StandardError
  false
end

def is_i?(s)
  /\A[-+]?\d+\z/ === s
end

def convert(s)
  return s.to_i if is_i? s
  return s.to_f if is_f? s
  s
end

label_proc = :to_s # default is to use strings for labels
OptionParser.new do |opts|
  opts.banner = "Usage: #{$PROGRAM_NAME} [--symbols] designfile.csv basecase.yml"
  opts.on('--symbols', "Generate labels as symbols (default = strings)") { label_proc = :to_sym }
end.parse!

design = File.open(ARGV.shift).readlines.map { |line| line.strip.split(/[\s,]+/) }
raise 'Missing header line?' if design[0].any? { |item| is_f?(item) || is_i?(item) }

labels = design.shift.map(&label_proc)

YAML.load_stream(ARGF) do |model_data|
  design.each do |design_pt|
    labels.each_with_index { |key, i| model_data[key] = convert(design_pt[i]) }
    puts model_data.to_yaml
  end
end
