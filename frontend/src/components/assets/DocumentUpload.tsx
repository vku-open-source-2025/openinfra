import { useState, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import { assetsApi } from "../../api/assets";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Upload, X } from "lucide-react";

interface DocumentUploadProps {
  assetId: string;
  onUploadComplete?: () => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ assetId, onUploadComplete }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [documentType, setDocumentType] = useState("");
  const [isPublic, setIsPublic] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      return assetsApi.uploadDocument(assetId, file, documentType || undefined, isPublic);
    },
    onSuccess: () => {
      onUploadComplete?.();
    },
  });

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files);
      setFiles((prev) => [...prev, ...newFiles]);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      setFiles((prev) => [...prev, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    for (const file of files) {
      await uploadMutation.mutateAsync(file);
    }
    setFiles([]);
    setDocumentType("");
    setIsPublic(false);
  };

  return (
    <div className="space-y-4">
      {/* Drag & Drop Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive ? "border-blue-500 bg-blue-50" : "border-slate-300 bg-white"
        }`}
      >
        <Upload className="mx-auto mb-4 text-slate-400" size={48} />
        <p className="text-sm text-slate-600 mb-2">
          Kéo thả tập tin vào đây, hoặc nhấp để chọn
        </p>
        <input
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          id="file-upload"
        />
        <label htmlFor="file-upload">
          <Button variant="outline" as="span">
            Chọn tập tin
          </Button>
        </label>
      </div>

      {/* Selected Files */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-slate-900">Tập tin đã chọn</h4>
          {files.map((file, index) => (
            <div
              key={index}
              className="flex items-center justify-between bg-slate-50 p-3 rounded border border-slate-200"
            >
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-900">{file.name}</span>
                <span className="text-xs text-slate-500">
                  ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeFile(index)}
                className="text-red-600 hover:text-red-700"
              >
                <X size={14} />
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Upload Options */}
      {files.length > 0 && (
        <div className="space-y-4 bg-slate-50 p-4 rounded-lg">
          <div>
            <label className="text-xs text-slate-500 uppercase tracking-wide mb-1 block">
              Loại tài liệu (tùy chọn)
            </label>
            <Input
              type="text"
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              placeholder="ví dụ: Hướng dẫn sử dụng, Chứng chỉ, Ảnh"
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is-public"
              checked={isPublic}
              onChange={(e) => setIsPublic(e.target.checked)}
              className="rounded border-slate-300"
            />
            <label htmlFor="is-public" className="text-sm text-slate-700">
              Công khai tài liệu (hiển thị cho công dân qua QR/NFC)
            </label>
          </div>
          <Button
            onClick={handleUpload}
            disabled={uploadMutation.isPending}
            className="w-full"
          >
            {uploadMutation.isPending ? "Đang tải lên..." : `Tải lên ${files.length} tệp`}
          </Button>
        </div>
      )}
    </div>
  );
};
