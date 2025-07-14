import React, { useState } from 'react';  
import axios from 'axios';
import { motion } from 'framer-motion';
import { FiUploadCloud } from 'react-icons/fi';
import { BsChevronDown, BsChevronUp } from 'react-icons/bs';

function UploadThreatCSV() {
  const [file, setFile] = useState(null);
  const [threats, setThreats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState({});

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
  };

  const toggleExpand = (index) => {
    setExpanded((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  const handleUpload = async () => {
    if (!file) return setError("Please select a CSV file.");

    const formData = new FormData();
    formData.append("file", file);
    setLoading(true);
    setError('');

    try {
      const response = await axios.post("http://localhost:5000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      console.log("Response from backend:", response.data);

      const data = response.data;

      if (Array.isArray(data)) {
        setThreats(data);
      } else if (Array.isArray(data.threats)) {
        setThreats(data.threats);
      } else {
        setError("Unexpected response format.");
      }
    } catch (err) {
      console.error(err);
      setError("Upload failed. Check backend and CSV.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white font-sans p-6">
      {/* Header */}
      <header className="flex items-center justify-between mb-10">
        <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-teal-400 via-blue-500 to-purple-500 bg-clip-text text-transparent">
          🛡️ Test Case Generator
        </h1>
      </header>

      {/* Upload Section */}
      <div className="bg-white/5 p-6 rounded-xl shadow-lg border border-gray-700 mb-10">
        <div className="flex items-center space-x-4">
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="bg-gray-900 text-white border border-gray-600 rounded px-4 py-2"
          />
          <button
            onClick={handleUpload}
            disabled={loading}
            className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-2 rounded-xl text-white font-semibold hover:from-indigo-500 hover:to-purple-500 transition"
          >
            <FiUploadCloud size={20} />
            {loading ? "Processing..." : "Upload CSV"}
          </button>
        </div>
        {error && <p className="text-red-400 mt-2">{error}</p>}
      </div>

      {/* Threat Cards */}
      <div className="grid md:grid-cols-2 gap-6">
        {threats.map((threat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 + index * 0.1 }}
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6 shadow-md border border-gray-700"
          >
            <div className="mb-4">
              <h2 className="text-xl font-bold text-cyan-400 mb-1">🔐 Title:</h2>
              <p className="text-white mb-3">{threat.title || "Untitled Threat"}</p>

              <h3 className="text-lg font-semibold text-yellow-400">Description:</h3>
              <p className="text-gray-300 text-sm">{threat.description || "No description provided."}</p>
            </div>

            {/* Vulnerabilities */}
            <div className="mt-4">
              <h3 className="text-lg font-semibold mb-2 text-pink-400">Vulnerabilities</h3>
              <div className="space-y-3">
                {threat.vulnerabilities?.map((vuln, vIndex) => (
                  <div
                    key={vIndex}
                    className="bg-gray-800/80 p-4 rounded-lg border border-gray-600"
                  >
                    <div
                      className="flex justify-between items-center cursor-pointer"
                      onClick={() => toggleExpand(`${index}-${vIndex}`)}
                    >
                      <p className="text-white font-medium">{vuln.description}</p>
                      {expanded[`${index}-${vIndex}`] ? <BsChevronUp /> : <BsChevronDown />}
                    </div>

                    {expanded[`${index}-${vIndex}`] && (
                      <ul className="list-decimal ml-6 mt-3 text-sm text-gray-300 space-y-1">
                        {vuln.test_cases?.map((tc, i) => (
                          <li key={i} className="pl-2">{tc}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Footer */}
      <footer className="mt-16 text-center text-gray-500 text-sm border-t border-gray-700 pt-6">
        Built with ❤️ for secure applications. | © {new Date().getFullYear()}
      </footer>
    </div>
  );
}

export default UploadThreatCSV;
