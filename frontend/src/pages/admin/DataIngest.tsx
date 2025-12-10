import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { ingestApi } from "../../api/ingest";
import { Button } from "../../components/ui/button";
import { Form, FormField, FormLabel, FormError } from "../../components/ui/form";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from "lucide-react";

const DataIngest: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const uploadMutation = useMutation({
    mutationFn: (file: File) => ingestApi.uploadCSV(file),
    onSuccess: (data) => {
      setSelectedFile(null);
      setErrors({});
      // Show success message
      alert(data.message || "Tải lên CSV thành công!");
    },
    onError: (error: any) => {
      if (error.response?.data?.detail) {
        setErrors({ submit: error.response.data.detail });
      } else {
        setErrors({ submit: "Tải CSV thất bại. Vui lòng thử lại." });
      }
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    setErrors({});

    if (!file) {
      return;
    }

    // Validate file type
    if (!file.name.endsWith(".csv")) {
      setErrors({ file: "Vui lòng chọn tệp CSV" });
      setSelectedFile(null);
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setErrors({ file: "Kích thước tệp phải nhỏ hơn 10MB" });
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    if (!selectedFile) {
      setErrors({ file: "Vui lòng chọn tệp CSV" });
      return;
    }

    uploadMutation.mutate(selectedFile);
  };

  const handleReset = () => {
    setSelectedFile(null);
    setErrors({});
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Nạp dữ liệu</h1>
        <p className="text-slate-500 mt-1">
          Tải tệp CSV để nhập hàng loạt tài sản vào hệ thống
        </p>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Tải tệp CSV</h2>

        <Form onSubmit={handleSubmit}>
          <FormField>
            <FormLabel required>Tệp CSV</FormLabel>
            <div className="mt-2">
              <label
                htmlFor="csv-upload"
                className="flex flex-col items-center justify-center w-full h-32 border-2 border-slate-300 border-dashed rounded-lg cursor-pointer bg-slate-50 hover:bg-slate-100 transition-colors"
              >
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  {selectedFile ? (
                    <>
                      <FileText className="w-10 h-10 mb-2 text-slate-400" />
                      <p className="mb-2 text-sm font-semibold text-slate-700">
                        {selectedFile.name}
                      </p>
                      <p className="text-xs text-slate-500">
                        {(selectedFile.size / 1024).toFixed(2)} KB
                      </p>
                    </>
                  ) : (
                    <>
                      <Upload className="w-10 h-10 mb-2 text-slate-400" />
                      <p className="mb-2 text-sm text-slate-500">
                        <span className="font-semibold">Nhấn để tải lên</span> hoặc kéo thả tệp
                      </p>
                      <p className="text-xs text-slate-500">Chỉ hỗ trợ CSV (tối đa 10MB)</p>
                    </>
                  )}
                </div>
                <input
                  id="csv-upload"
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={handleFileChange}
                  disabled={uploadMutation.isPending}
                />
              </label>
            </div>
            {errors.file && <FormError>{errors.file}</FormError>}
            {selectedFile && (
              <div className="mt-2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleReset}
                  className="text-sm text-slate-600 hover:text-slate-800"
                  disabled={uploadMutation.isPending}
                >
                  Xóa tệp
                </button>
              </div>
            )}
          </FormField>

          {errors.submit && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-800">Tải lên thất bại</p>
                <p className="text-sm text-red-600">{errors.submit}</p>
              </div>
            </div>
          )}

          {uploadMutation.isSuccess && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-green-800">Tải lên thành công</p>
                <p className="text-sm text-green-600">
                  {uploadMutation.data?.message || "Đã xử lý tệp CSV thành công"}
                </p>
              </div>
            </div>
          )}

          <div className="flex gap-4 mt-6">
            <Button
              type="submit"
              disabled={!selectedFile || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Đang tải lên...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Tải CSV
                </>
              )}
            </Button>
            {selectedFile && (
              <Button
                type="button"
                variant="outline"
                onClick={handleReset}
                disabled={uploadMutation.isPending}
              >
                Hủy
              </Button>
            )}
          </div>
        </Form>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">Yêu cầu định dạng CSV</h3>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>Tệp phải ở định dạng CSV (đuôi .csv)</li>
          <li>Kích thước tối đa: 10MB</li>
          <li>Các cột bắt buộc: asset_code, name, feature_type, feature_code, latitude, longitude</li>
          <li>Các cột tùy chọn: category, status, address, properties</li>
          <li>Hệ thống sẽ xử lý tệp bất đồng bộ</li>
        </ul>
      </div>
    </div>
  );
};

export default DataIngest;
