export async function importProducts(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("http://127.0.0.1:8000/import/products", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Import failed");
  }

  return response.json();
}
