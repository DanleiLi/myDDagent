import { useRef, useState } from 'react'

interface UploadZoneProps {
  onUpload: (file: File) => Promise<void>
  disabled?: boolean
}

export function UploadZone({ onUpload, disabled }: UploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0 || uploading) return
    setUploading(true)
    try {
      for (const file of Array.from(files)) {
        await onUpload(file)
      }
    } catch (err) {
      console.error('Upload error:', err)
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    if (!disabled) handleFiles(e.dataTransfer.files)
  }

  return (
    <div
      onClick={() => !disabled && !uploading && inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setIsDragOver(true) }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
      className="flex items-center justify-center rounded-lg text-xs cursor-pointer transition-colors"
      style={{
        border: `1px dashed ${isDragOver ? 'var(--accent)' : 'var(--border)'}`,
        backgroundColor: isDragOver ? 'rgba(16,163,127,0.05)' : 'transparent',
        color: 'var(--text-secondary)',
        height: '64px',
        opacity: disabled ? 0.5 : 1,
        cursor: disabled ? 'not-allowed' : 'pointer',
      }}
    >
      {uploading ? 'Uploading…' : 'Drop files here or click to upload'}
      <input
        ref={inputRef}
        type="file"
        multiple
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
    </div>
  )
}
