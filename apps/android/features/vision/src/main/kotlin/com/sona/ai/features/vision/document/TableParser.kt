package com.sona.ai.features.vision.document

import com.sona.ai.features.vision.TableData
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Parses tabular data from OCR text output.
 * Supports pipe-separated (|) and tab-separated formats.
 */
@Singleton
class TableParser @Inject constructor() {

    /**
     * Parse tables from raw text content.
     * Detects delimiter type (pipe or tab) and extracts structured table data.
     *
     * @param text Raw text potentially containing table data
     * @return List of [TableData] found in the text
     */
    fun parseTable(text: String): List<TableData> {
        val lines = text.lines().filter { it.contains("|") || it.contains("\t") }
        if (lines.isEmpty()) return emptyList()

        val tables = mutableListOf<TableData>()
        val separator = if (lines.first().contains("|")) "|" else "\t"

        val parsed = lines
            .map { line ->
                line.split(separator)
                    .map { cell -> cell.trim() }
                    .filter { cell -> cell.isNotEmpty() }
            }
            .filter { it.isNotEmpty() }
            // Filter out markdown separator lines (e.g., "---", "----")
            .filter { row -> !row.all { cell -> cell.matches(Regex("^-+$")) } }

        if (parsed.size >= 2) {
            tables.add(
                TableData(
                    headers = parsed.first(),
                    rows = parsed.drop(1)
                )
            )
        }

        return tables
    }

    /**
     * Parse a table from CSV-formatted text.
     *
     * @param csvText CSV text content
     * @return [TableData] or null if parsing fails
     */
    fun parseCsv(csvText: String): TableData? {
        val lines = csvText.lines().filter { it.isNotBlank() }
        if (lines.size < 2) return null

        val parsed = lines.map { line ->
            line.split(",").map { it.trim().removeSurrounding("\"") }
        }

        return TableData(
            headers = parsed.first(),
            rows = parsed.drop(1)
        )
    }
}
