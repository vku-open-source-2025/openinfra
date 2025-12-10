import React, { useRef } from 'react';
import QRCode from 'react-qr-code';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { X, Download } from 'lucide-react';
import { type Asset, getAssetId } from '../api';

interface QRCodeModalProps {
    isOpen: boolean;
    onClose: () => void;
    asset: Asset | null;
}

const QRCodeModal: React.FC<QRCodeModalProps> = ({ isOpen, onClose, asset }) => {
    const qrRef = useRef<HTMLDivElement>(null);

    if (!isOpen || !asset) return null;

    const handleDownloadPDF = async () => {
        if (!qrRef.current) return;

        try {
            const canvas = await html2canvas(qrRef.current);
            const imgData = canvas.toDataURL('image/png');

            const pdf = new jsPDF({
                orientation: 'portrait',
                unit: 'mm',
                format: 'a6' // Small format
            });

            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = pdf.internal.pageSize.getHeight();

            // Add Title
            pdf.setFontSize(14);
            pdf.text('Mã QR tài sản', pdfWidth / 2, 15, { align: 'center' });

            // Add Asset Info
            pdf.setFontSize(10);
            pdf.text(`ID: ${getAssetId(asset)}`, pdfWidth / 2, 25, { align: 'center' });
            pdf.text(`Loại: ${asset.feature_type}`, pdfWidth / 2, 30, { align: 'center' });

            // Add QR Image
            const imgWidth = 60;
            const imgHeight = 60;
            const x = (pdfWidth - imgWidth) / 2;
            const y = 40;

            pdf.addImage(imgData, 'PNG', x, y, imgWidth, imgHeight);

            // Add Footer
            pdf.setFontSize(8);
            pdf.text('OpenInfra Asset Management', pdfWidth / 2, pdfHeight - 10, { align: 'center' });

            pdf.save(`asset-qr-${getAssetId(asset)}.pdf`);
        } catch (err) {
            console.error("Lỗi khi tạo PDF:", err);
            alert("Tạo PDF thất bại");
        }
    };

    return (
        <div className="fixed inset-0 z-9999 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-sm overflow-hidden animate-in fade-in zoom-in duration-200">
                <div className="flex justify-between items-center p-4 border-b border-slate-100">
                    <h3 className="font-bold text-lg text-slate-800">Mã QR tài sản</h3>
                    <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-8 flex flex-col items-center gap-6">
                    <div ref={qrRef} className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                        <QRCode
                            value={`https://openinfra.space/map?assetId=${getAssetId(asset)}`}
                            size={200}
                            level="H"
                        />
                    </div>

                    <div className="text-center">
                        <p className="font-bold text-slate-800">{asset.feature_type}</p>
                        <p className="text-xs text-slate-500 font-mono mt-1">{getAssetId(asset)}</p>
                        <p className="text-[10px] text-slate-400 mt-1 truncate max-w-[200px]">https://openinfra.space/map?assetId={getAssetId(asset)}</p>
                    </div>

                    <button
                        onClick={handleDownloadPDF}
                        className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors shadow-sm"
                    >
                        <Download size={18} />
                        Tải xuống PDF
                    </button>
                </div>
            </div>
        </div>
    );
};

export default QRCodeModal;
