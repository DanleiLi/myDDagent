"""
Data Cleaner for JSON output
Removes work dump artifacts and produces clean, validated data
"""

from typing import List, Dict, Any, Set
from collections import Counter


class DataCleaner:
    """Cleans and validates JSON data before output."""

    def clean(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Clean records and return structured output with metadata.

        Returns:
            {
                'data': cleaned records,
                'metadata': {
                    'original_count': int,
                    'cleaned_count': int,
                    'rows_removed': int,
                    'columns': list of column names,
                    'quality_score': float (0-1)
                }
            }
        """
        if not records:
            return {'data': [], 'metadata': self._empty_metadata()}

        original_count = len(records)

        # Step 1: Remove empty rows
        non_empty = [r for r in records if not self._is_empty_row(r)]

        # Step 2: Get all valid columns (remove columns that are all None)
        valid_columns = self._get_valid_columns(non_empty)

        # Step 3: Prune records to valid columns and clean values
        pruned = []
        for record in non_empty:
            cleaned_record = {}
            for col in valid_columns:
                value = record.get(col)
                cleaned_value = self._clean_value(value)
                # Only include non-None values or if explicitly wanted
                if cleaned_value is not None:
                    cleaned_record[col] = cleaned_value
                else:
                    cleaned_record[col] = None
            pruned.append(cleaned_record)

        # Step 4: Normalize types by column (attempt to maintain consistency)
        normalized = self._normalize_types(pruned, valid_columns)

        # Step 5: Calculate quality metrics
        rows_removed = original_count - len(normalized)
        quality_score = self._calculate_quality_score(
            original_count, len(normalized), valid_columns
        )

        metadata = {
            'original_count': original_count,
            'cleaned_count': len(normalized),
            'rows_removed': rows_removed,
            'columns': valid_columns,
            'column_count': len(valid_columns),
            'quality_score': quality_score
        }

        return {
            'data': normalized,
            'metadata': metadata
        }

    def _is_empty_row(self, record: Dict[str, Any]) -> bool:
        """Check if a row has any non-None values."""
        return all(v is None or v == '' for v in record.values())

    def _get_valid_columns(self, records: List[Dict[str, Any]]) -> List[str]:
        """Get columns that have at least one non-None value."""
        if not records:
            return []

        # Collect all columns
        all_columns = set()
        for record in records:
            all_columns.update(record.keys())

        # Filter to columns with at least one non-None value
        valid = []
        for col in sorted(all_columns):
            if any(record.get(col) is not None for record in records):
                valid.append(col)

        return valid

    def _clean_value(self, value: Any) -> Any:
        """Clean a single value."""
        if value is None:
            return None

        if isinstance(value, str):
            # Strip whitespace
            cleaned = value.strip()
            # Return None if empty after stripping
            return cleaned if cleaned else None

        return value

    def _normalize_types(self, records: List[Dict[str, Any]],
                        columns: List[str]) -> List[Dict[str, Any]]:
        """Attempt to normalize data types consistently within each column."""
        if not records:
            return []

        # Determine expected type for each column
        column_types = {}
        for col in columns:
            types_found = Counter()
            for record in records:
                value = record.get(col)
                if value is not None:
                    types_found[type(value).__name__] += 1

            # Use most common type as target
            if types_found:
                column_types[col] = types_found.most_common(1)[0][0]

        # Normalize values to target types
        normalized = []
        for record in records:
            normalized_record = {}
            for col in columns:
                value = record.get(col)
                target_type = column_types.get(col)
                normalized_value = self._coerce_type(value, target_type)
                normalized_record[col] = normalized_value
            normalized.append(normalized_record)

        return normalized

    def _coerce_type(self, value: Any, target_type: str) -> Any:
        """Attempt to coerce value to target type."""
        if value is None:
            return None

        if target_type == 'NoneType':
            return None

        if target_type == 'int':
            try:
                if isinstance(value, bool):
                    return value
                return int(float(str(value)))
            except (ValueError, TypeError):
                return value

        if target_type == 'float':
            try:
                if isinstance(value, bool):
                    return value
                return float(value)
            except (ValueError, TypeError):
                return value

        if target_type == 'bool':
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ['true', 'yes', '1', 'on']
            return bool(value)

        # Default to string
        return str(value)

    def _calculate_quality_score(self, original: int, cleaned: int,
                                columns: List[str]) -> float:
        """
        Calculate data quality score (0-1).
        Based on retention rate and column count.
        """
        if original == 0:
            return 1.0

        retention = cleaned / original

        # Penalize if too many rows removed or too few columns
        penalty = 0
        if retention < 0.5:  # Lost more than 50% of rows
            penalty += 0.3 * (1 - retention)
        if len(columns) == 0:  # No valid columns
            return 0.0

        return max(0.0, min(1.0, retention - penalty))

    def _empty_metadata(self) -> Dict[str, Any]:
        """Return empty metadata structure."""
        return {
            'original_count': 0,
            'cleaned_count': 0,
            'rows_removed': 0,
            'columns': [],
            'column_count': 0,
            'quality_score': 1.0
        }
