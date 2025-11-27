import React, { useState, useEffect, useRef } from 'react';
import { X, Smartphone, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import type { Asset } from '../api';

type NDEFReadingEvent = any;


interface NFCWriteModalProps {
    isOpen: boolean;
    onClose: () => void;
    asset: Asset | null;
}

const NFCWriteModal: React.FC<NFCWriteModalProps> = ({ isOpen, onClose, asset }) => {
    const [status, setStatus] = useState<'idle' | 'scanning' | 'writing' | 'success' | 'error'>('idle');
    const [message, setMessage] = useState<string>('');
    const abortControllerRef = useRef<AbortController | null>(null);

    useEffect(() => {
        if (isOpen && asset) {
            startScanning();
        } else {
            stopScanning();
        }

        return () => stopScanning();
    }, [isOpen, asset]);

    const stopScanning = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        setStatus('idle');
    };

    const startScanning = async () => {
        if (!('NDEFReader' in window)) {
            setStatus('error');
            setMessage('Web NFC is not supported on this device/browser.');
            return;
        }

        setStatus('scanning');
        setMessage('Ready to scan. Tap your device on the NFC tag.');

        abortControllerRef.current = new AbortController();

        try {
            // @ts-ignore - NDEFReader is experimental
            const ndef = new NDEFReader();
            await ndef.scan({ signal: abortControllerRef.current.signal });

            ndef.onreading = async (_event: NDEFReadingEvent) => {
                setStatus('writing');
                setMessage('Tag detected. Writing data...');

                try {
                    const url = `https://openinfra.space/map?assetId=${asset?._id}`;

                    // Write URL record
                    await ndef.write({
                        records: [{ recordType: "url", data: url }]
                    });

                    setStatus('success');
                    setMessage('Successfully wrote asset URL to NFC tag!');

                    // Auto close after success
                    setTimeout(() => {
                        onClose();
                    }, 2000);

                } catch (writeError) {
                    console.error(writeError);
                    setStatus('error');
                    setMessage('Failed to write to tag. Please try again.');
                }
            };

            ndef.onreadingerror = () => {
                setStatus('error');
                setMessage('Error reading tag. Please try again.');
            };

        } catch (error) {
            console.error(error);
            setStatus('error');
            setMessage('Failed to start NFC scan. Ensure NFC is enabled.');
        }
    };

    if (!isOpen || !asset) return null;

    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-sm overflow-hidden animate-in fade-in zoom-in duration-200">
                <div className="flex justify-between items-center p-4 border-b border-slate-100">
                    <h3 className="font-bold text-lg text-slate-800">Write to NFC</h3>
                    <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-8 flex flex-col items-center gap-6 text-center">
                    <div className={`w-24 h-24 rounded-full flex items-center justify-center transition-colors duration-300 ${status === 'scanning' ? 'bg-blue-100 text-blue-600 animate-pulse' :
                        status === 'writing' ? 'bg-amber-100 text-amber-600 animate-pulse' :
                            status === 'success' ? 'bg-green-100 text-green-600' :
                                status === 'error' ? 'bg-red-100 text-red-600' :
                                    'bg-slate-100 text-slate-400'
                        }`}>
                        {status === 'scanning' && <Smartphone size={48} />}
                        {status === 'writing' && <Loader2 size={48} className="animate-spin" />}
                        {status === 'success' && <CheckCircle size={48} />}
                        {status === 'error' && <AlertCircle size={48} />}
                        {status === 'idle' && <Smartphone size={48} />}
                    </div>

                    <div>
                        <h4 className="font-bold text-slate-800 text-lg mb-2">
                            {status === 'scanning' ? 'Ready to Scan' :
                                status === 'writing' ? 'Writing Data...' :
                                    status === 'success' ? 'Success!' :
                                        status === 'error' ? 'Error' : 'Initialize'}
                        </h4>
                        <p className="text-slate-500 text-sm">
                            {message}
                        </p>
                    </div>

                    {status === 'error' && (
                        <button
                            onClick={startScanning}
                            className="px-6 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium transition-colors"
                        >
                            Try Again
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default NFCWriteModal;
