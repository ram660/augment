"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { documentsAPI } from "@/lib/api/documents";

export default function DocumentsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<"generic" | "contractor_quote" | "datasheet" | "inspection">("generic");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null;
    setFile(f);
  };

  const onAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let data: any;
      if (docType === "generic") {
        data = await documentsAPI.parse(file);
      } else if (docType === "contractor_quote") {
        data = await documentsAPI.parseContractorQuote(file);
      } else if (docType === "datasheet") {
        data = await documentsAPI.parseDatasheet(file);
      } else {
        data = await documentsAPI.parseInspection(file);
      }
      setResult(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Failed to parse document");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Document Analyzer</h1>
        <p className="text-sm text-gray-600">Upload a PDF/image/text file to extract structured data using MarkItDown.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upload & Analyze</CardTitle>
          <CardDescription>Select a document type to improve extraction quality for your use case.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col md:flex-row gap-3 md:items-center">
            <input
              type="file"
              accept="application/pdf,image/*,text/plain"
              onChange={onFileChange}
              className="border rounded px-3 py-2"
            />
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value as any)}
              className="border rounded px-3 py-2 w-full md:w-64"
            >
              <option value="generic">Generic</option>
              <option value="contractor_quote">Contractor Quote</option>
              <option value="datasheet">Product Datasheet</option>
              <option value="inspection">Inspection Report</option>
            </select>
            <Button onClick={onAnalyze} disabled={!file || loading}>
              {loading ? "Analyzing…" : "Analyze"}
            </Button>
          </div>

          {error && (
            <div className="text-sm text-red-600">{error}</div>
          )}

          {result && (
            <div className="mt-4 space-y-4">
              {result.parsed?.summary && (
                <div className="p-3 rounded bg-blue-50 border border-blue-200 text-blue-900 text-sm">
                  Summary: {result.parsed.summary}
                </div>
              )}

              {/* Contractor Quote view */}
              {Array.isArray(result.parsed?.items) && (
                <div>
                  <h3 className="font-semibold mb-2">Items</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead>
                        <tr className="text-left border-b">
                          {Object.keys(result.parsed.items[0] || { description: "Description", total: "Total" }).map((k) => (
                            <th key={k} className="py-2 pr-4 capitalize">{k}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {result.parsed.items.map((it: any, idx: number) => (
                          <tr key={idx} className="border-b">
                            {Object.keys(result.parsed.items[0] || it).map((k) => (
                              <td key={k} className="py-2 pr-4">{String(it[k] ?? "")}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Totals */}
              {result.parsed?.totals && (
                <div className="text-sm">
                  <h3 className="font-semibold mb-1">Totals</h3>
                  <pre className="bg-gray-50 border rounded p-3 overflow-auto">{JSON.stringify(result.parsed.totals, null, 2)}</pre>
                </div>
              )}

              {/* Markdown Preview */}
              {result.parsed?.markdown && (
                <div className="text-sm">
                  <h3 className="font-semibold mb-1">Markdown</h3>
                  <pre className="bg-gray-50 border rounded p-3 overflow-auto max-h-80 whitespace-pre-wrap">{result.parsed.markdown}</pre>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

