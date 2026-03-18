# PII Detection Software

A comprehensive Python tool for detecting Personally Identifiable Information (PII) in CSV files using Microsoft Presidio and GLiNER.

## Features

- **Dual Engine Approach**: Combines Microsoft Presidio and GLiNER for improved accuracy
- **Indian-Specific PII Detection**: Specialized recognizers for Aadhaar numbers and PAN cards
- **Comprehensive Reporting**: JSON and CSV output formats with detailed statistics
- **Data Anonymization**: Optional anonymization of detected PII using Presidio
- **CLI Interface**: Easy-to-use command-line interface
- **Progress Tracking**: Real-time progress updates and logging

## Supported PII Types

### Standard PII Types
- **PERSON**: Names and personal identifiers
- **EMAIL_ADDRESS**: Email addresses
- **PHONE_NUMBER**: Phone numbers (including Indian formats)
- **ADDRESS**: Physical addresses
- **LOCATION**: Geographic locations
- **ORGANIZATION**: Company and organization names
- **DATE_TIME**: Dates and time information
- **ID**: General identification numbers

### Indian-Specific PII Types
- **AADHAAR**: 12-digit Aadhaar numbers
- **PAN**: PAN card numbers (ABCDE1234F format)
- **PHONE_NUMBER**: Indian phone formats (+91, 0 prefix, etc.)

## Installation

### Prerequisites

**Important**: This project requires **Python 3.10 or 3.11** for best compatibility. Python 3.12+ may have dependency issues.

### Quick Setup (Recommended)

**Windows:**
1. Install Python 3.10 or 3.11 from [python.org](https://python.org)
2. Run the setup script:
   ```bash
   setup.bat
   ```

**Linux/macOS:**
1. Install Python 3.10 or 3.11
2. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

### Manual Setup

1. **Clone or download the project:**
```bash
git clone <repository-url>
cd PII-Detection-software
```

2. **Create virtual environment:**
```bash
python -m venv venv
```

3. **Activate virtual environment:**
```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Download spaCy model:**
```bash
python -m spacy download en_core_web_sm
```

6. **Verify installation:**
```bash
python main.py --help
```

### Troubleshooting

**If you encounter build errors:**
- Ensure you're using Python 3.10 or 3.11
- Use the provided setup script
- Install in a clean virtual environment

**Compiler errors (gcc/clang not found):**
- The setup script uses pre-compiled wheels to avoid compiler issues
- If problems persist, try: `pip install --only-binary=all -r requirements.txt`

## Usage

### Basic Usage

```bash
# Analyze a CSV file
python main.py --input data.csv --output report.json

# Generate both JSON and CSV reports
python main.py -i data.csv -o report.json -c csv_reports/

# Analyze with sample size (for large files)
python main.py -i data.csv -o report.json --sample-size 1000

# Disable GLiNER engine (faster processing)
python main.py -i data.csv -o report.json --no-gliner
```

### Advanced Usage

```bash
# Anonymize detected PII
python main.py -i data.csv -o report.json --anonymize anonymized_data.csv

# Use different GLiNER model
python main.py -i data.csv -o report.json --gliner-model "urchade/gliner_multi-v2.1"

# Quiet mode (minimal output)
python main.py -i data.csv -o report.json --quiet

# Debug mode (verbose logging)
python main.py -i data.csv -o report.json --log-level DEBUG
```

### Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--input` | `-i` | Input CSV file path (required) |
| `--output` | `-o` | Output JSON report path (default: pii_report.json) |
| `--csv-output` | `-c` | Output directory for CSV reports |
| `--anonymize` | `-a` | Path to save anonymized CSV |
| `--sample-size` | `-s` | Number of rows to sample per column |
| `--no-gliner` | | Disable GLiNER engine |
| `--gliner-model` | | GLiNER model name |
| `--log-level` | | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `--quiet` | `-q` | Suppress console output |

## Project Structure

```
PII-Detection-software/
├── main.py                      # Main CLI interface
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── pii_detector/               # Core detection modules
│   ├── presidio_engine.py       # Presidio engine with Indian PII recognizers
│   ├── gliner_engine.py        # GLiNER engine for additional entity detection
│   ├── utils.py                # Utility functions for data processing
│   └── report_generator.py     # Report generation (JSON/CSV)
└── sample_data/                # Sample CSV files for testing
    └── test_data.csv           # Test data with various PII types
```

## Output Formats

### JSON Report Structure

```json
{
  "metadata": {
    "input_file": "data.csv",
    "total_rows": 1000,
    "total_columns": 10,
    "processing_time_seconds": 45.2,
    "engines_used": ["presidio", "gliner"],
    "report_generated_at": "2024-03-17T11:22:00",
    "report_version": "1.0"
  },
  "columns": [
    {
      "name": "email",
      "is_pii": true,
      "pii_types": ["EMAIL_ADDRESS"],
      "pii_percentage": 92.5,
      "total_rows": 1000,
      "pii_rows": 925,
      "avg_confidence": 0.95
    }
  ],
  "rows": [
    {
      "row": 1,
      "column": "email",
      "value": "user@example.com",
      "pii_detected": true,
      "entity": "EMAIL_ADDRESS",
      "confidence": 0.98,
      "source_engine": "presidio"
    }
  ],
  "summary": {
    "total_columns": 10,
    "pii_columns": 4,
    "pii_column_percentage": 40.0,
    "total_rows_processed": 1000,
    "total_pii_detections": 2500,
    "pii_type_distribution": {
      "EMAIL_ADDRESS": 925,
      "PERSON": 800,
      "PHONE_NUMBER": 500,
      "AADHAAR": 275
    },
    "avg_confidence_score": 0.87,
    "most_common_pii_type": "EMAIL_ADDRESS"
  }
}
```

### CSV Reports

When using `--csv-output`, three CSV files are generated:

1. **pii_column_summary.csv**: Column-level PII statistics
2. **pii_row_details.csv**: Row-level detection results
3. **pii_summary_stats.csv**: Overall summary statistics

## Sample Data

The project includes a sample CSV file (`sample_data/test_data.csv`) with various PII types for testing:

- Names and email addresses
- Phone numbers (US and Indian formats)
- Physical addresses
- Aadhaar numbers (12-digit)
- PAN card numbers
- Ages and company names
- General text notes

## Performance Considerations

### Processing Speed
- **Presidio only**: Faster processing, good for standard PII types
- **Presidio + GLiNER**: Slower but more comprehensive detection
- **Sample size**: Use `--sample-size` for large files to reduce processing time

### Memory Usage
- Large CSV files are processed column by column to minimize memory usage
- GLiNER model loading requires additional memory (~500MB)

### Accuracy vs Speed Trade-off
- For quick scans: Use `--no-gliner` flag
- For comprehensive analysis: Use both engines (default)

## Error Handling

The tool includes comprehensive error handling for:

- Invalid CSV files
- Encoding issues (tries multiple encodings)
- Missing or corrupted data
- Model loading failures
- File permission issues

## Logging

The tool generates detailed logs in `pii_detection.log` with information about:

- Processing progress
- Detection results
- Errors and warnings
- Performance metrics

## Examples

### Example 1: Basic Analysis
```bash
python main.py -i sample_data/test_data.csv -o test_report.json
```

Expected output:
```
🔍 Analyzing PII in: sample_data/test_data.csv
🤖 Using engines: presidio, gliner
✅ JSON report saved to: test_report.json

==================================================
PII DETECTION REPORT SUMMARY
==================================================
Input File: sample_data/test_data.csv
Processing Time: 12.5 seconds
Engines Used: presidio, gliner

Column Statistics:
  Total Columns: 9
  PII Columns: 7 (77.78%)
  Non-PII Columns: 2

Row Statistics:
  Total Rows Processed: 20
  Total PII Detections: 85
  Average Confidence: 0.891

PII Type Distribution:
  EMAIL_ADDRESS: 20
  PERSON: 20
  PHONE_NUMBER: 20
  AADHAAR: 10
  PAN: 5
==================================================
```

### Example 2: Large File Processing
```bash
python main.py -i large_dataset.csv -o large_report.json -c reports/ --sample-size 5000
```

### Example 3: Anonymization
```bash
python main.py -i sensitive_data.csv -o report.json --anonymize anonymized_data.csv
```

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:

1. Check the log file `pii_detection.log` for detailed error messages
2. Verify input CSV format and encoding
3. Ensure all dependencies are properly installed
4. Test with the provided sample data first

## Technical Details

### Presidio Integration
- Uses `AnalyzerEngine` for PII detection
- Custom recognizers for Indian PII types
- `AnonymizerEngine` for data anonymization

### GLiNER Integration
- Uses HuggingFace GLiNER model for generalized NER
- Complements Presidio with additional entity types
- Configurable model selection

### Data Processing
- Pandas for CSV handling
- Multiple encoding support
- Memory-efficient processing
- Progress tracking with tqdm

## Dependencies

- `pandas>=1.5.0`: Data manipulation
- `presidio-analyzer>=2.2.0`: PII analysis
- `presidio-anonymizer>=2.2.0`: Data anonymization
- `gliner>=0.2.6`: Generalized NER
- `tqdm>=4.64.0`: Progress bars
- `click>=8.0.0`: CLI interface
- `python-dotenv>=0.19.0`: Environment variables
