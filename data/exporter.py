"""
Data Exporter Module
Handles exporting of scraped data to various file formats.
"""

import logging
import os
import csv
import json
from typing import List, Dict, Any, Optional, Union
import time

logger = logging.getLogger(__name__)

class DataExporter:
    def __init__(self):
        """Initialize the data exporter."""
        logger.info("Data exporter initialized")

    def export(self, data: List[Dict[str, Any]], format_type: str = 'csv', 
              output_path: Optional[str] = None) -> str:
        """
        Export data to the specified format.
        
        Args:
            data (list): List of data items to export
            format_type (str, optional): Format to export to ('csv', 'excel', 'json'). Defaults to 'csv'.
            output_path (str, optional): Path to save the output file. Defaults to None.
            
        Returns:
            str: Path to the exported file
        """
        if not data:
            logger.warning("No data to export")
            return self._create_empty_file(format_type, output_path)
            
        logger.info(f"Exporting {len(data)} data items to {format_type} format")
        
        # Normalize format type
        format_type = format_type.lower()
        
        try:
            # Choose export method based on format type
            if format_type == 'csv':
                return self.export_csv(data, output_path)
            elif format_type == 'excel':
                return self.export_excel(data, output_path)
            elif format_type == 'json':
                return self.export_json(data, output_path)
            else:
                logger.warning(f"Unsupported format type: {format_type}, defaulting to CSV")
                return self.export_csv(data, output_path)
                
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            # Create an error file with the error message
            error_path = self._get_output_path('error.txt', output_path)
            with open(error_path, 'w') as f:
                f.write(f"Error exporting data: {str(e)}")
            return error_path

    def _create_empty_file(self, format_type: str, output_path: Optional[str] = None) -> str:
        """
        Create an empty file of the specified format.
        
        Args:
            format_type (str): Format type ('csv', 'excel', 'json')
            output_path (str, optional): Output path. Defaults to None.
            
        Returns:
            str: Path to the empty file
        """
        logger.warning("Creating empty file as there is no data to export")
        
        if format_type == 'csv':
            path = self._get_output_path('empty.csv', output_path)
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['no_data'])
            return path
            
        elif format_type == 'excel':
            try:
                import pandas as pd
                
                path = self._get_output_path('empty.xlsx', output_path)
                df = pd.DataFrame({'no_data': []})
                df.to_excel(path, index=False)
                return path
                
            except ImportError:
                logger.error("Pandas not installed, cannot create empty Excel file")
                path = self._get_output_path('empty.csv', output_path)
                with open(path, 'w') as f:
                    f.write('no_data\n')
                return path
                
        elif format_type == 'json':
            path = self._get_output_path('empty.json', output_path)
            with open(path, 'w') as f:
                json.dump([], f)
            return path
            
        else:
            path = self._get_output_path('empty.txt', output_path)
            with open(path, 'w') as f:
                f.write('No data to export\n')
            return path

    def _get_output_path(self, default_filename: str, output_path: Optional[str] = None) -> str:
        """
        Get the output file path.
        
        Args:
            default_filename (str): Default filename to use if output_path is a directory or None
            output_path (str, optional): Specified output path. Defaults to None.
            
        Returns:
            str: Complete output file path
        """
        if not output_path:
            # Use current directory with default filename
            timestamp = int(time.time())
            return os.path.join(os.getcwd(), f"{timestamp}_{default_filename}")
            
        # Check if output_path is a directory
        if os.path.isdir(output_path):
            timestamp = int(time.time())
            return os.path.join(output_path, f"{timestamp}_{default_filename}")
            
        # If path has no extension, append the appropriate one
        if '.' not in os.path.basename(output_path):
            ext = os.path.splitext(default_filename)[1]
            return f"{output_path}{ext}"
            
        # Otherwise, use the provided path as is
        return output_path

    def export_csv(self, data: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
        """
        Export data to CSV format.
        
        Args:
            data (list): List of data items to export
            output_path (str, optional): Path to save the CSV file. Defaults to None.
            
        Returns:
            str: Path to the exported CSV file
        """
        # Get the output path
        path = self._get_output_path('data.csv', output_path)
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        
        try:
            # Get all field names from all items
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            
            # Sort field names for consistent output
            fieldnames = sorted(fieldnames)
            
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in data:
                    # Clean item for CSV export
                    clean_item = {}
                    for key, value in item.items():
                        if isinstance(value, (list, dict)):
                            # Convert complex types to JSON strings
                            clean_item[key] = json.dumps(value)
                        else:
                            clean_item[key] = value
                            
                    writer.writerow(clean_item)
            
            logger.info(f"Data exported to CSV: {path}")
            return path
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise

    def export_excel(self, data: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
        """
        Export data to Excel format.
        
        Args:
            data (list): List of data items to export
            output_path (str, optional): Path to save the Excel file. Defaults to None.
            
        Returns:
            str: Path to the exported Excel file
        """
        # Get the output path
        path = self._get_output_path('data.xlsx', output_path)
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        
        try:
            # Check if pandas is installed
            try:
                import pandas as pd
            except ImportError:
                logger.error("Pandas not installed, falling back to CSV export")
                return self.export_csv(data, path.replace('.xlsx', '.csv'))
            
            # Get all field names
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            
            # Convert data to a format compatible with pandas
            processed_data = []
            for item in data:
                processed_item = {}
                for key in fieldnames:
                    if key in item:
                        if isinstance(item[key], (list, dict)):
                            # Convert complex types to JSON strings
                            processed_item[key] = json.dumps(item[key])
                        else:
                            processed_item[key] = item[key]
                    else:
                        processed_item[key] = None
                processed_data.append(processed_item)
            
            # Create DataFrame and export to Excel
            df = pd.DataFrame(processed_data)
            df.to_excel(path, index=False)
            
            logger.info(f"Data exported to Excel: {path}")
            return path
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            # Fallback to CSV export
            logger.info("Falling back to CSV export")
            return self.export_csv(data, path.replace('.xlsx', '.csv'))

    def export_json(self, data: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
        """
        Export data to JSON format.
        
        Args:
            data (list): List of data items to export
            output_path (str, optional): Path to save the JSON file. Defaults to None.
            
        Returns:
            str: Path to the exported JSON file
        """
        # Get the output path
        path = self._get_output_path('data.json', output_path)
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data exported to JSON: {path}")
            return path
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")
            raise

    def export_multiple_formats(self, data: List[Dict[str, Any]], 
                               formats: List[str] = ['csv', 'json'],
                               output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Export data to multiple formats.
        
        Args:
            data (list): List of data items to export
            formats (list, optional): List of formats to export to. Defaults to ['csv', 'json'].
            output_dir (str, optional): Directory to save the output files. Defaults to None.
            
        Returns:
            dict: Dictionary mapping format types to output paths
        """
        if not data:
            logger.warning("No data to export")
            return {fmt: self._create_empty_file(fmt, output_dir) for fmt in formats}
            
        logger.info(f"Exporting {len(data)} data items to multiple formats: {formats}")
        
        # Generate base filename
        timestamp = int(time.time())
        filename_base = f"data_{timestamp}"
        
        result = {}
        
        for fmt in formats:
            try:
                if fmt.lower() == 'csv':
                    output_path = os.path.join(output_dir, f"{filename_base}.csv") if output_dir else None
                    result['csv'] = self.export_csv(data, output_path)
                    
                elif fmt.lower() == 'excel':
                    output_path = os.path.join(output_dir, f"{filename_base}.xlsx") if output_dir else None
                    result['excel'] = self.export_excel(data, output_path)
                    
                elif fmt.lower() == 'json':
                    output_path = os.path.join(output_dir, f"{filename_base}.json") if output_dir else None
                    result['json'] = self.export_json(data, output_path)
                    
                else:
                    logger.warning(f"Unsupported format: {fmt}, skipping")
                    
            except Exception as e:
                logger.error(f"Error exporting to {fmt}: {str(e)}")
                # Continue with other formats
        
        return result

    def split_and_export(self, data: List[Dict[str, Any]], chunk_size: int = 1000,
                        format_type: str = 'csv', output_dir: Optional[str] = None) -> List[str]:
        """
        Split data into chunks and export each chunk.
        
        Args:
            data (list): List of data items to export
            chunk_size (int, optional): Size of each chunk. Defaults to 1000.
            format_type (str, optional): Format to export to. Defaults to 'csv'.
            output_dir (str, optional): Directory to save the output files. Defaults to None.
            
        Returns:
            list: List of paths to the exported files
        """
        if not data:
            logger.warning("No data to export")
            return [self._create_empty_file(format_type, output_dir)]
            
        # Calculate number of chunks
        num_chunks = (len(data) + chunk_size - 1) // chunk_size
        
        logger.info(f"Splitting {len(data)} items into {num_chunks} chunks of size {chunk_size}")
        
        output_paths = []
        
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(data))
            
            chunk = data[start_idx:end_idx]
            
            # Generate filename for this chunk
            timestamp = int(time.time())
            filename_base = f"data_{timestamp}_part{i+1}of{num_chunks}"
            
            if format_type == 'csv':
                output_path = os.path.join(output_dir, f"{filename_base}.csv") if output_dir else None
                path = self.export_csv(chunk, output_path)
                
            elif format_type == 'excel':
                output_path = os.path.join(output_dir, f"{filename_base}.xlsx") if output_dir else None
                path = self.export_excel(chunk, output_path)
                
            elif format_type == 'json':
                output_path = os.path.join(output_dir, f"{filename_base}.json") if output_dir else None
                path = self.export_json(chunk, output_path)
                
            else:
                logger.warning(f"Unsupported format: {format_type}, defaulting to CSV")
                output_path = os.path.join(output_dir, f"{filename_base}.csv") if output_dir else None
                path = self.export_csv(chunk, output_path)
            
            output_paths.append(path)
            
        return output_paths