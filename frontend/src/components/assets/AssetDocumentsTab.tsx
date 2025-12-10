import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { assetsApi } from "../../api/assets";
import { format } from "date-fns";
import { Skeleton } from "../ui/skeleton";
import { Button } from "../ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Upload, Download, Eye, FileText, Image, File, X } from "lucide-react";
import { DocumentUpload } from "./DocumentUpload";
import type { AssetAttachment } from "../../types/asset";

interface AssetDocumentsTabProps {
  assetId: string;
}

const AssetDocumentsTab: React.FC<AssetDocumentsTabProps> = ({ assetId }) => {
  const queryClient = useQueryClient();
  const [showUpload, setShowUpload] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<AssetAttachment | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  const { data: documents, isLoading } = useQuery({
    queryKey: ["asset", "documents", assetId],
    queryFn: () => assetsApi.getDocuments(assetId),
  });

  const deleteMutation = useMutation({
    mutationFn: (attachmentUrl: string) => assetsApi.deleteAttachment(assetId, attachmentUrl),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["asset", "documents", assetId] });
    },
  });

  const getFileIcon = (fileType: string) => {
    if (fileType.startsWith("image/")) return Image;
    if (fileType.includes("pdf")) return FileText;
    return File;
  };

  const handlePreview = (doc: AssetAttachment) => {
    setSelectedDocument(doc);
    setShowPreview(true);
  };

  const handleDownload = (doc: AssetAttachment) => {
    window.open(doc.file_url, "_blank");
  };

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <div className="bg-slate-50 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-900">Tải lên tài liệu</h3>
          <Button onClick={() => setShowUpload(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Tải tài liệu lên
          </Button>
        </div>
        <DocumentUpload
          assetId={assetId}
          onUploadComplete={() => {
            queryClient.invalidateQueries({ queryKey: ["asset", "documents", assetId] });
            setShowUpload(false);
          }}
        />
      </div>

      {/* Document List */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : documents && documents.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Loại</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Tên</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Phiên bản</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Người tải lên</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Ngày</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Hành động</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {documents.map((doc, idx) => {
                const FileIcon = getFileIcon(doc.file_type);

                return (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <FileIcon size={20} className="text-slate-400" />
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-slate-900">{doc.file_name}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">
                      {doc.version ? `v${doc.version}` : "v1"}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">{doc.uploaded_by}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">
                      {format(new Date(doc.uploaded_at), "dd/MM/yyyy")}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handlePreview(doc)}
                        >
                          <Eye size={14} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDownload(doc)}
                        >
                          <Download size={14} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteMutation.mutate(doc.file_url)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <X size={14} />
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 text-slate-500">
          <FileText size={48} className="mx-auto mb-4 opacity-50" />
          <p>Chưa có tài liệu được tải lên.</p>
        </div>
      )}

      {/* Preview Modal */}
      {selectedDocument && (
        <Dialog open={showPreview} onOpenChange={setShowPreview}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{selectedDocument.file_name}</DialogTitle>
            </DialogHeader>
            <div className="mt-4">
              {selectedDocument.file_type.startsWith("image/") ? (
                <img
                  src={selectedDocument.file_url}
                  alt={selectedDocument.file_name}
                  className="max-w-full h-auto rounded"
                />
              ) : (
                <div className="bg-slate-50 rounded-lg p-8 text-center">
                  <FileText size={64} className="mx-auto mb-4 text-slate-400" />
                  <p className="text-slate-600 mb-4">Xem trước không có sẵn cho loại tệp này.</p>
                  <Button onClick={() => handleDownload(selectedDocument)}>
                    <Download className="h-4 w-4 mr-2" />
                    Tải xuống
                  </Button>
                </div>
              )}
              <div className="mt-4 pt-4 border-t border-slate-200">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <label className="text-xs text-slate-500 uppercase tracking-wide">Loại tệp</label>
                    <p className="text-slate-900 mt-1">{selectedDocument.file_type}</p>
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 uppercase tracking-wide">Ngày tải lên</label>
                    <p className="text-slate-900 mt-1">
                      {format(new Date(selectedDocument.uploaded_at), "dd/MM/yyyy HH:mm")}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 uppercase tracking-wide">Người tải lên</label>
                    <p className="text-slate-900 mt-1">{selectedDocument.uploaded_by}</p>
                  </div>
                  {selectedDocument.version && (
                    <div>
                      <label className="text-xs text-slate-500 uppercase tracking-wide">Phiên bản</label>
                      <p className="text-slate-900 mt-1">v{selectedDocument.version}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default AssetDocumentsTab;
