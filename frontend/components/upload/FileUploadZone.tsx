"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useRouter } from "next/navigation";
import { UploadCloud, AlertCircle, X, Sparkles, FileText, File as FileIcon } from "lucide-react";
import { useReviewStore } from "@/store/reviewStore";

const ACCEPTED_TYPES = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
    ".docx",
  ],
};

const MAX_SIZE = 10 * 1024 * 1024; // 10 MB

export default function FileUploadZone() {
  const router = useRouter();
  const {
    uploadDocument,
    startDocumentReview,
    uploadProgress,
    isUploading,
    error,
    clearError,
  } = useReviewStore();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      clearError();
      setFileError(null);

      if (rejectedFiles.length > 0) {
        const rejection = rejectedFiles[0];
        if (rejection.errors[0]?.code === "file-too-large") {
          setFileError("File is too large. Maximum size is 10 MB.");
        } else if (rejection.errors[0]?.code === "file-invalid-type") {
          setFileError("Unsupported file type. Only PDF and DOCX files are accepted.");
        } else {
          setFileError(rejection.errors[0]?.message || "File validation failed.");
        }
        return;
      }

      if (acceptedFiles.length > 0) {
        setSelectedFile(acceptedFiles[0]);
      }
    },
    [clearError]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_SIZE,
    multiple: false,
  });

  const handleUploadAndReview = async () => {
    if (!selectedFile) return;

    const fileId = await uploadDocument(selectedFile);
    if (!fileId) return;

    const reviewId = await startDocumentReview(fileId);
    if (reviewId) {
      router.push(`/review/${reviewId}`);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (type: string) => (type === "application/pdf" ? FileText : FileIcon);

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`upload-zone ${isDragActive ? "upload-zone-active" : ""}`}
        id="file-upload-zone"
      >
        <input {...getInputProps()} id="file-input" />

        {/* Upload Icon */}
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-brand-500/10 to-purple-500/10 flex items-center justify-center mb-6">
          <UploadCloud
            className={`w-10 h-10 text-brand-400 transition-transform duration-300 ${
              isDragActive ? "scale-110" : ""
            }`}
            strokeWidth={1.5}
          />
        </div>

        {isDragActive ? (
          <p className="text-lg font-medium text-brand-400">
            Drop your SOW document here...
          </p>
        ) : (
          <>
            <p className="text-lg font-medium text-gray-200 mb-2">
              Drag & drop your SOW document
            </p>
            <p className="text-sm text-gray-500">
              or click to browse • PDF, DOCX • Max 10 MB
            </p>
          </>
        )}
      </div>

      {/* File Error */}
      {fileError && (
        <div className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" strokeWidth={2} />
          {fileError}
        </div>
      )}

      {/* API Error */}
      {error && (
        <div className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" strokeWidth={2} />
          {error}
        </div>
      )}

      {/* Selected File Preview */}
      {selectedFile && !isUploading && (
        <div className="mt-6 glass-card p-5 animate-slide-up">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {(() => {
                const Icon = getFileIcon(selectedFile.type);
                return <Icon className="w-8 h-8 text-brand-400" strokeWidth={1.5} />;
              })()}
              <div>
                <p className="font-medium text-gray-200">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {formatFileSize(selectedFile.size)} •{" "}
                  {selectedFile.type === "application/pdf" ? "PDF" : "DOCX"}
                </p>
              </div>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
              }}
              className="p-2 hover:bg-white/5 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" strokeWidth={2} />
            </button>
          </div>

          <button
            onClick={handleUploadAndReview}
            className="btn-primary w-full mt-4"
            id="start-review-btn"
          >
            <Sparkles className="w-5 h-5" strokeWidth={2} />
            Start AI Review
          </button>
        </div>
      )}

      {/* Upload Progress */}
      {isUploading && (
        <div className="mt-6 glass-card p-5 animate-fade-in">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-5 h-5 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm font-medium text-gray-300">
              {uploadProgress < 100
                ? `Uploading... ${uploadProgress}%`
                : "Starting AI review..."}
            </span>
          </div>
          <div className="w-full h-2 rounded-full bg-surface-700 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-brand-500 to-purple-500 transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
