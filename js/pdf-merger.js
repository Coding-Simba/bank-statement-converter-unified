// PDF Merger Backend Functionality
// Uses PDF-lib library for PDF manipulation

class PDFMerger {
    constructor() {
        this.files = [];
        this.mergedPdf = null;
        this.initializeEventListeners();
        this.loadPDFLib();
    }

    async loadPDFLib() {
        // Load PDF-lib library dynamically
        if (!window.PDFLib) {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js';
            script.onload = () => {
                console.log('PDF-lib loaded successfully');
            };
            document.head.appendChild(script);
        }
    }

    initializeEventListeners() {
        const mergeArea = document.getElementById('mergeArea');
        const fileInput = document.getElementById('fileInput');
        const chooseFilesBtn = document.getElementById('chooseFilesBtn');

        if (mergeArea) {
            // Drag and drop functionality
            mergeArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                mergeArea.classList.add('drag-over');
            });

            mergeArea.addEventListener('dragleave', () => {
                mergeArea.classList.remove('drag-over');
            });

            mergeArea.addEventListener('drop', (e) => {
                e.preventDefault();
                mergeArea.classList.remove('drag-over');
                this.handleFiles(e.dataTransfer.files);
            });

            mergeArea.addEventListener('click', () => {
                fileInput.click();
            });
        }

        if (chooseFilesBtn) {
            chooseFilesBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                fileInput.click();
            });
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFiles(e.target.files);
            });
        }
    }

    handleFiles(files) {
        const pdfFiles = Array.from(files).filter(file => 
            file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
        );

        if (pdfFiles.length === 0) {
            this.showMessage('Please select PDF files only', 'error');
            return;
        }

        this.files = pdfFiles;
        this.displaySelectedFiles();
    }

    displaySelectedFiles() {
        const container = document.querySelector('.upload-container');
        
        // Remove existing file list if present
        const existingList = container.querySelector('.selected-files');
        if (existingList) {
            existingList.remove();
        }

        // Create file list UI
        const fileListDiv = document.createElement('div');
        fileListDiv.className = 'selected-files';
        fileListDiv.innerHTML = `
            <h3 style="margin: 30px 0 20px; color: #1a1a1a;">Selected Files (${this.files.length})</h3>
            <div class="file-list" style="max-width: 600px; margin: 0 auto;">
                ${this.files.map((file, index) => `
                    <div class="file-item" style="background: #f8f9fa; padding: 15px; margin-bottom: 10px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <i class="fas fa-file-pdf" style="color: #667eea;"></i>
                            <span>${file.name}</span>
                            <span style="color: #6c757d; font-size: 0.875rem;">(${this.formatFileSize(file.size)})</span>
                        </div>
                        <button class="remove-file" data-index="${index}" style="background: none; border: none; color: #dc3545; cursor: pointer;">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `).join('')}
            </div>
            <div style="margin-top: 30px; display: flex; gap: 15px; justify-content: center;">
                <button id="addMoreFiles" style="background: white; color: #667eea; border: 2px solid #667eea; padding: 12px 30px; border-radius: 8px; font-weight: 600; cursor: pointer;">
                    <i class="fas fa-plus"></i> Add More Files
                </button>
                <button id="mergeFiles" style="background: #667eea; color: white; border: none; padding: 12px 40px; border-radius: 8px; font-weight: 600; cursor: pointer;">
                    <i class="fas fa-layer-group"></i> Merge PDFs
                </button>
            </div>
            <div id="mergeProgress" style="display: none; margin-top: 30px;">
                <div style="background: #e7e5fb; border-radius: 8px; height: 8px; overflow: hidden;">
                    <div id="progressBar" style="background: #667eea; height: 100%; width: 0%; transition: width 0.3s ease;"></div>
                </div>
                <p style="text-align: center; margin-top: 10px; color: #667eea;">Merging PDFs... <span id="progressText">0%</span></p>
            </div>
        `;

        container.appendChild(fileListDiv);

        // Add event listeners
        document.querySelectorAll('.remove-file').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(btn.dataset.index);
                this.removeFile(index);
            });
        });

        document.getElementById('addMoreFiles')?.addEventListener('click', (e) => {
            e.stopPropagation();
            document.getElementById('fileInput').click();
        });

        document.getElementById('mergeFiles')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.mergePDFs();
        });
    }

    removeFile(index) {
        this.files.splice(index, 1);
        if (this.files.length > 0) {
            this.displaySelectedFiles();
        } else {
            document.querySelector('.selected-files')?.remove();
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async mergePDFs() {
        if (this.files.length < 2) {
            this.showMessage('Please select at least 2 PDF files to merge', 'error');
            return;
        }

        // Check if PDF-lib is loaded
        if (!window.PDFLib) {
            this.showMessage('PDF library is still loading. Please try again in a moment.', 'info');
            return;
        }

        const { PDFDocument } = window.PDFLib;

        // Show progress
        const progressDiv = document.getElementById('mergeProgress');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        progressDiv.style.display = 'block';

        try {
            // Create a new PDF document
            const mergedPdf = await PDFDocument.create();
            let totalPages = 0;
            let processedPages = 0;

            // First, count total pages
            for (const file of this.files) {
                const arrayBuffer = await file.arrayBuffer();
                const pdf = await PDFDocument.load(arrayBuffer);
                totalPages += pdf.getPageCount();
            }

            // Merge all PDFs
            for (let fileIndex = 0; fileIndex < this.files.length; fileIndex++) {
                const file = this.files[fileIndex];
                const arrayBuffer = await file.arrayBuffer();
                const pdf = await PDFDocument.load(arrayBuffer);
                const pages = await mergedPdf.copyPages(pdf, pdf.getPageIndices());
                
                pages.forEach((page) => {
                    mergedPdf.addPage(page);
                    processedPages++;
                    const progress = Math.round((processedPages / totalPages) * 100);
                    progressBar.style.width = progress + '%';
                    progressText.textContent = progress + '%';
                });
            }

            // Save the merged PDF
            const mergedPdfBytes = await mergedPdf.save();
            
            // Create download link
            this.downloadMergedPDF(mergedPdfBytes);
            
            // Hide progress
            setTimeout(() => {
                progressDiv.style.display = 'none';
                this.showMessage('PDFs merged successfully!', 'success');
            }, 500);

        } catch (error) {
            console.error('Error merging PDFs:', error);
            progressDiv.style.display = 'none';
            this.showMessage('Error merging PDFs. Please ensure all files are valid PDFs.', 'error');
        }
    }

    downloadMergedPDF(pdfBytes) {
        const blob = new Blob([pdfBytes], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        const timestamp = new Date().toISOString().slice(0, 10);
        const filename = `merged_statements_${timestamp}.pdf`;

        // Create download button
        const downloadDiv = document.createElement('div');
        downloadDiv.style.cssText = 'margin-top: 30px; text-align: center;';
        downloadDiv.innerHTML = `
            <button id="downloadMerged" style="background: #28a745; color: white; border: none; padding: 15px 40px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 1.125rem;">
                <i class="fas fa-download"></i> Download Merged PDF
            </button>
            <p style="margin-top: 15px; color: #6c757d;">File size: ${this.formatFileSize(pdfBytes.length)}</p>
        `;

        const container = document.querySelector('.selected-files');
        const existingDownload = container.querySelector('#downloadMerged')?.parentElement;
        if (existingDownload) {
            existingDownload.remove();
        }
        container.appendChild(downloadDiv);

        // Add download functionality
        document.getElementById('downloadMerged').addEventListener('click', () => {
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            // Clean up after download
            setTimeout(() => {
                URL.revokeObjectURL(url);
            }, 100);
        });
    }

    showMessage(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;

        const colors = {
            'success': '#28a745',
            'error': '#dc3545',
            'info': '#17a2b8'
        };

        messageDiv.style.background = colors[type] || colors.info;
        messageDiv.textContent = message;
        document.body.appendChild(messageDiv);

        setTimeout(() => {
            messageDiv.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => messageDiv.remove(), 300);
        }, 3000);
    }
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .merge-area.drag-over {
        background: linear-gradient(135deg, #7b88ec 0%, #8457a8 100%) !important;
        transform: scale(1.02);
    }
    
    .remove-file:hover {
        transform: scale(1.1);
    }
    
    #addMoreFiles:hover {
        background: #667eea !important;
        color: white !important;
    }
    
    #mergeFiles:hover {
        background: #5968d9 !important;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
    }
    
    #downloadMerged:hover {
        background: #218838 !important;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(40, 167, 69, 0.3);
    }
`;
document.head.appendChild(style);

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new PDFMerger();
    });
} else {
    new PDFMerger();
}