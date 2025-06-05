import React, { useState } from 'react';

const Inicio = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleDelete = (index) => { 
   setFiles((prevFiles) => prevFiles.filter((_, i) => i !== index));
  }

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length > 10) {
      setError("Solo puedes subir hasta 10 archivos.");
      return;
    }
    setFiles(selectedFiles);
    setError(null);
  };

 const handleSubmit = async (e) => {
  e.preventDefault();
  if (files.length === 0) {
    setError("Por favor selecciona al menos un archivo.");
    return;
  }

  setLoading(true);
  setError(null);

  try {
    for (const file of files) {
      const response = await fetch("http://127.0.0.1:8081/generate-signed-url", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          file_name: file.name,
          content_type: file.type
        })
      });

      if (!response.ok) {
        throw new Error("No se pudo generar la URL de subida.");
      }

      const data = await response.json();
      console.log("URL de subida generada:", data);
      const signedUrl = data.signed_url;

      const uploadResponse = await fetch(signedUrl, {
        method: "PUT",
        headers: {
          "Content-Type": file.type
        },
        body: file
      });

      if (!uploadResponse.ok) {
        throw new Error(`Error al subir el archivo ${file.name}`);
      }
    }

    alert("¡Archivos subidos exitosamente!");
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
};


  return (
    <>
      <main
        className='w-full h-screen'
        style={{
          backgroundImage: "linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%)"
        }}
      >
        <div className='flex flex-col items-center justify-center h-full gap-8'>
          <h1 className='text-3xl font-bold text-center my-10'>
            <span className='text-blue-500'>Accessa</span> - Automatización de Reportes
          </h1>

          <form
            onSubmit={handleSubmit}
            className='flex flex-col items-center gap-4'
            encType="multipart/form-data"
          >
            <div className='flex items-center gap-2'>
              <label htmlFor="file">Elegir archivos</label>
              <input
                className='border rounded-xs border-blue-200 max-w-64'
                id='file'
                type="file"
                name="files"
                multiple
                onChange={handleFileChange}
              />
             
             
            </div>
             {files.length > 0 && (
                <ul className='mt-2 text-left'>
                  {files.map((file, index) => (
                    <li key={index} className='flex items-center gap-2 text-gray-700'>
                      <svg xmlns="http://www.w3.org/2000/svg" width={24} height={24} viewBox="0 0 24 24">
	<path fill="currentColor" d="M14 11a3 3 0 0 1-3-3V4H7a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-8zm-2-3a2 2 0 0 0 2 2h3.59L12 4.41zM7 3h5l7 7v9a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V6a3 3 0 0 1 3-3"></path>
</svg> {file.name}
<button onClick={() => handleDelete(index)} className='flex items-center cursor-pointer'>
    <svg xmlns="http://www.w3.org/2000/svg" width={20} height={20} viewBox="0 0 24 24">
	<path fill="#ff221899" d="M19 6.41L17.59 5L12 10.59L6.41 5L5 6.41L10.59 12L5 17.59L6.41 19L12 13.41L17.59 19L19 17.59L13.41 12z"></path>
</svg>
</button>
                    </li>
                  ))}
                </ul>
              )}
             <small className='text-gray-600'>Selecciona hasta 10 archivos</small>
            {error && <p className='text-red-500'>{error}</p>}
            <button
              className='cursor-pointer border flex items-center gap-2 rounded-md bg-blue-400 px-4 py-2'
              type="submit"
              disabled={loading}
            >
              {loading ? "Subiendo..." : "Subir archivos"}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width={24}
                height={24}
                viewBox="0 0 24 24"
              >
                <path
                  fill="currentColor"
                  d="M8.71 7.71L11 5.41V15a1 1 0 0 0 2 0V5.41l2.29 2.3a1 1 0 0 0 1.42 0a1 1 0 0 0 0-1.42l-4-4a1 1 0 0 0-.33-.21a1 1 0 0 0-.76 0a1 1 0 0 0-.33.21l-4 4a1 1 0 1 0 1.42 1.42M21 12a1 1 0 0 0-1 1v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-6a1 1 0 0 0-2 0v6a3 3 0 0 0 3 3h14a3 3 0 0 0 3-3v-6a1 1 0 0 0-1-1"
                ></path>
              </svg>
            </button>
          </form>
        </div>
      </main>
    </>
  );
};

export default Inicio;
