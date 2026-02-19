UPDATE suppliers 
SET is_approved = true 
WHERE id IN (
    SELECT supplier_id 
    FROM invoices 
    WHERE ocr_status IN ('completed', 'verified')
);
