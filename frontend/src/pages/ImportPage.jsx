import { useState } from "react";
import { importProducts } from "../services/importService";
import Papa from "papaparse";
import * as XLSX from "xlsx";
import "./ImportProducts.css";

function ImportPage() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [previewRows, setPreviewRows] = useState([]);
  const [previewHeaders, setPreviewHeaders] = useState([]);
  const [isImporting, setIsImporting] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleFilePreview = (file) => {
    const fileName = file.name.toLowerCase();

    if (fileName.endsWith(".csv")) {
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          setPreviewHeaders(results.meta.fields || []);
          setPreviewRows(results.data.slice(0, 5));
        },
      });
    }

    else if (fileName.endsWith(".xlsx")) {
      const reader = new FileReader();

      reader.onload = (e) => {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: "array" });

        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];

        const jsonData = XLSX.utils.sheet_to_json(worksheet, {
          defval: "", 
        });

        if (jsonData.length > 0) {
          setPreviewHeaders(Object.keys(jsonData[0]));
          setPreviewRows(jsonData.slice(0, 5));
        }
      };

      reader.readAsArrayBuffer(file);
    }

    else {
      alert("Unsupported file type. Please upload CSV or XLSX.");
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setFile(file);

    handleFilePreview(file);
  };

  const handleImport = async () => {
    if (!file) {
      alert("Please select a CSV or Excel file");
      return;
    }

    setIsImporting(true);
    setProgress(10);

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      setProgress(30);

      const resp = await fetch("http://127.0.0.1:8000/import/products", {
        method: "POST",
        body: formData,
      });

      setProgress(70);

      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(text || "Import failed");
      }

      const response = await resp.json();
      console.log("response is ", response);

      if (response.errors && response.errors.length > 0) {
        setError(response.errors);
      }

      setResult(response);
      setProgress(100);
    } catch (err) {
      console.log("error is ", err);
      setError(err.message || "Import failed");
    } finally {
      setTimeout(() => {
        setIsImporting(false);
        setProgress(0);
      }, 1000);
      setLoading(false);
    }
  };

  const handleDownload = async() => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/import/products/result/${result.download_id}`);
      console.log('download endpoint response ', response);
      if (!response.ok) {
      throw new Error("Download failed");
    }

    const blob = await response.blob();

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "import_results.xlsx";
    document.body.appendChild(a);
    a.click();


    a.remove();
    window.URL.revokeObjectURL(url);

    }
    catch(err) {
      console.log('error in dwnld endpoint ', err)
    }
  }

  return (
    <div style={{ maxWidth: '100%' }}>
      <h2>Import Products</h2>

      <input type="file" accept=".csv,.xlsx,.xls" onChange={handleFileChange} />

      {previewRows.length > 0 && (
        <div style={{ marginTop: "20px" }}>
          <h3>File Preview (first 5 rows)</h3>

          <div style={{ overflowX: "auto" }}>
            <table
              border="1"
              cellPadding="6"
              style={{ borderCollapse: "collapse" }}
            >
              <thead>
                <tr>
                  {previewHeaders.map((h) => (
                    <th key={h}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewRows.map((row, idx) => (
                  <tr key={idx}>
                    {previewHeaders.map((h) => (
                      <td key={h}>{row[h]}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div style={{ marginTop: 12 }}>
        <button onClick={handleImport} disabled={loading}>
          {loading ? "Importing..." : "Start Import"}
        </button>
      </div>

      {isImporting && (
        <div className="progress-container">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          {loading && <p className="progress-text">Loading...</p>}
        </div>
      )}

      {error?.length > 0 && Array.isArray(error) && (
        <div className="error-box">
          <h3>⚠️ Validation Errors</h3>
          <p>
            Some rows were skipped because they failed validation. Fix the
            errors below and re-upload the file.
          </p>

          <ul>
            {error.map((err, index) => (
              <li key={index}>
                <strong>{err.product || "Unknown product"}</strong>
                <ul>
                  {err.errors?.map((msg, i) => (
                    <li key={i}>{msg}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </div>
      )}

      {result && (
        <>
          <div style={{ marginTop: 24 }}>
            <h3>Import Summary</h3>

            <ul>
              <li>Products Created: {result.products_created}</li>
              <li>Products Updated: {result.products_updated}</li>
              <li>Variants Created: {result.variants_created}</li>
              <li>Variants Updated: {result.variants_updated}</li>
            </ul>
            
          </div>
          {result.download_id && <button onClick={handleDownload}>Download Import Result</button>}
        </>
      )}
    </div>
  );
}

export default ImportPage;
