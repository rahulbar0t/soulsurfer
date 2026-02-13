import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Waves, CloudArrowUp, Video, CheckCircle, Warning } from '@phosphor-icons/react';
import { uploadVideo } from '../api';
import './UploadForm.css';

const ALLOWED_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm'];
const MAX_SIZE_MB = 100;

// Ripple effect hook
function useRipple() {
  const [ripples, setRipples] = useState([]);

  const addRipple = useCallback((e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const id = Date.now();

    setRipples(prev => [...prev, { x, y, id }]);
    setTimeout(() => {
      setRipples(prev => prev.filter(r => r.id !== id));
    }, 600);
  }, []);

  return { ripples, addRipple };
}

export default function UploadForm({ onSessionCreated }) {
  const [file, setFile] = useState(null);
  const [surferName, setSurferName] = useState('');
  const [skillLevel, setSkillLevel] = useState('');
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef(null);
  const { ripples, addRipple } = useRipple();

  function validateFile(f) {
    const ext = '.' + f.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported format "${ext}". Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`;
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File too large (${(f.size / 1024 / 1024).toFixed(1)} MB). Max: ${MAX_SIZE_MB} MB`;
    }
    return null;
  }

  function handleFile(f) {
    const err = validateFile(f);
    if (err) {
      setError(err);
      setFile(null);
    } else {
      setError('');
      setFile(f);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }

  function handleDragOver(e) {
    e.preventDefault();
    setDragging(true);
  }

  function handleDragLeave(e) {
    e.preventDefault();
    setDragging(false);
  }

  function handleInputChange(e) {
    const f = e.target.files[0];
    if (f) handleFile(f);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    addRipple(e);
    if (!file) return;

    setUploading(true);
    setError('');

    try {
      const session = await uploadVideo(file, surferName || null, skillLevel || null);
      onSessionCreated(session.session_id);
    } catch (err) {
      setError(err.message);
      setUploading(false);
    }
  }

  return (
    <motion.div
      className="upload-form"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
    >
      <div className="upload-header">
        <motion.h1
          className="brand-title"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          SoulSurfer
          <span className="brand-underline"></span>
        </motion.h1>
        <motion.p
          className="upload-subtitle"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          Upload your surf session and get personalized coaching from your AI surf coach
        </motion.p>
      </div>

      <form onSubmit={handleSubmit}>
        <motion.div
          className={`drop-zone ${dragging ? 'drop-zone--active' : ''} ${file ? 'drop-zone--has-file' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => inputRef.current?.click()}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3, duration: 0.4 }}
        >
          {/* Wave animation at bottom */}
          <div className="drop-zone__wave">
            <svg viewBox="0 0 1200 120" preserveAspectRatio="none">
              <path d="M0,60 C150,120 350,0 600,60 C850,120 1050,0 1200,60 L1200,120 L0,120 Z" />
            </svg>
          </div>

          <input
            ref={inputRef}
            type="file"
            accept={ALLOWED_EXTENSIONS.join(',')}
            onChange={handleInputChange}
            hidden
          />

          <AnimatePresence mode="wait">
            {file ? (
              <motion.div
                className="drop-zone__file-info"
                key="file-info"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ duration: 0.3 }}
              >
                <motion.div
                  className="drop-zone__icon-wrapper drop-zone__icon-wrapper--success"
                  initial={{ rotate: -180 }}
                  animate={{ rotate: 0 }}
                  transition={{ type: "spring", stiffness: 200 }}
                >
                  <CheckCircle weight="fill" size={48} />
                </motion.div>
                <span className="drop-zone__filename">{file.name}</span>
                <span className="drop-zone__size">
                  {(file.size / 1024 / 1024).toFixed(1)} MB
                </span>
                <span className="drop-zone__change">Click to change</span>
              </motion.div>
            ) : (
              <motion.div
                className="drop-zone__prompt"
                key="prompt"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <motion.div
                  className="drop-zone__icon-wrapper"
                  animate={{ y: [0, -8, 0] }}
                  transition={{
                    repeat: Infinity,
                    duration: 2.5,
                    ease: "easeInOut"
                  }}
                >
                  <CloudArrowUp weight="duotone" size={56} />
                </motion.div>
                <span className="drop-zone__text">Drag & drop your surf video here</span>
                <span className="drop-zone__or">or click to browse</span>
                <div className="drop-zone__formats">
                  <Video weight="fill" size={14} />
                  <span>MP4, MOV, AVI, MKV, WEBM</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        <motion.p
          className="upload-formats"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          Maximum file size: {MAX_SIZE_MB} MB
        </motion.p>

        <motion.div
          className="form-fields"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <div className="form-group">
            <label htmlFor="surfer-name">
              <Waves weight="fill" size={14} />
              Name <span className="optional-tag">optional</span>
            </label>
            <input
              id="surfer-name"
              type="text"
              placeholder="What should we call you?"
              value={surferName}
              onChange={(e) => setSurferName(e.target.value)}
              disabled={uploading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="skill-level">
              <Waves weight="fill" size={14} />
              Skill Level <span className="optional-tag">optional</span>
            </label>
            <select
              id="skill-level"
              value={skillLevel}
              onChange={(e) => setSkillLevel(e.target.value)}
              disabled={uploading}
            >
              <option value="">Select your level</option>
              <option value="beginner">Beginner (Catching whitewater)</option>
              <option value="intermediate">Intermediate (Riding green waves)</option>
              <option value="advanced">Advanced (Carving & aerials)</option>
            </select>
          </div>
        </motion.div>

        <AnimatePresence>
          {error && (
            <motion.div
              className="upload-error"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <Warning weight="fill" size={18} />
              <span>{error}</span>
            </motion.div>
          )}
        </AnimatePresence>

        <motion.button
          type="submit"
          className="submit-btn"
          disabled={!file || uploading}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {/* Ripple effects */}
          {ripples.map(ripple => (
            <span
              key={ripple.id}
              className="ripple"
              style={{ left: ripple.x, top: ripple.y }}
            />
          ))}

          <span className="submit-btn__text">
            {uploading ? (
              <>
                <span className="submit-btn__loader"></span>
                Paddling Out...
              </>
            ) : (
              <>
                <Waves weight="bold" size={20} />
                Analyze My Session
              </>
            )}
          </span>

          {/* Shimmer effect */}
          <span className="submit-btn__shimmer"></span>
        </motion.button>
      </form>
    </motion.div>
  );
}
