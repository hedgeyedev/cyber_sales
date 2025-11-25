# SharePoint Distribution Guide for HTML Reports

## ⚠️ Important: SharePoint Limitations

SharePoint has significant limitations for displaying HTML reports with JavaScript:
- HTML files **download instead of opening** in browser by default
- JavaScript execution may be blocked by Content Security Policy (CSP)
- External CDN resources (Chart.js) may require admin whitelisting
- Modern SharePoint pages don't support inline JavaScript without custom SPFx solutions

## 📋 Recommended Approaches (in order of preference)

### Option 1: SharePoint Document Library (Download-Based) ⭐ **SIMPLEST**

**How it works**: Users download ZIP, extract, and view locally

**Steps**:
1. Create a SharePoint document library (e.g., "Sales Reports")
2. Upload the generated ZIP file (`cyber_sales_reports_YYYYMMDD.zip`)
3. Add library description: "Download ZIP, extract, and open index.html"
4. Users download → extract → open index.html in browser

**Pros**:
- ✅ No admin permissions needed
- ✅ Charts work perfectly (viewed locally)
- ✅ Simple setup

**Cons**:
- ❌ Requires download/extract step
- ❌ Not viewable directly in SharePoint

---

### Option 2: Embed in SharePoint Page (Classic Sites) ⚠️ **REQUIRES CLASSIC SITE**

**Requirements**:
- Classic SharePoint site (not Modern)
- Script Editor web part enabled
- Site Collection Features: "SharePoint Server Publishing Infrastructure" activated

**Steps**:

1. **Enable Script Editor** (if not available):
   ```
   Site Settings → Site Collection Features →
   Activate "SharePoint Server Publishing Infrastructure"
   ```

2. **Create new page**:
   - Site Pages → New → Web Part Page
   - Choose layout (e.g., "Full Page Vertical")
   - Name: "Cyber Sales Dashboard"

3. **Add Script Editor web part**:
   - Edit page → Add Web Part
   - Media and Content → Script Editor → Add

4. **Embed report HTML**:
   - Click "Edit Snippet"
   - Copy entire HTML from one of your reports
   - Paste into editor
   - Click "Insert"
   - Save page

**Pros**:
- ✅ Reports viewable directly in SharePoint
- ✅ No download needed
- ✅ Charts work (if CSP allows)

**Cons**:
- ❌ Only works on Classic sites (not Modern)
- ❌ May be blocked by CSP policies
- ❌ Requires republishing for updates
- ❌ Script Editor may be disabled by admin

---

### Option 3: SharePoint Modern Page with Embed Web Part ⚠️ **LIMITED SUCCESS**

**Steps**:

1. **Host HTML files externally**:
   - Upload reports to Azure Blob Storage (with public access)
   - Or use GitHub Pages
   - Get public URL

2. **Create Modern page**:
   - Pages → New → Blank page
   - Title: "Cyber Sales Reports"

3. **Add Embed web part**:
   - Edit page → Add web part → Embed
   - Paste URL to your hosted HTML file
   - Save page

**Pros**:
- ✅ Works on Modern sites

**Cons**:
- ❌ Requires external hosting
- ❌ May be blocked by iframe restrictions
- ❌ CSP may block Chart.js CDN
- ❌ Additional infrastructure needed

---

### Option 4: Convert to PDF and Embed ⭐ **BEST SHAREPOINT COMPATIBILITY**

**How it works**: Convert HTML reports to PDF with rendered charts

**Steps**:

1. **Convert HTML to PDF** (use one of these tools):
   ```bash
   # Option A: Using wkhtmltopdf
   wkhtmltopdf --javascript-delay 2000 \
     cyber_november_comparison_2020_2025.html \
     cyber_sales_2020_2025.pdf

   # Option B: Using Puppeteer (Node.js)
   # See convert_to_pdf.js script

   # Option C: Using Chrome browser
   # Open HTML → Print → Save as PDF
   ```

2. **Upload PDFs to SharePoint**:
   - Create document library
   - Upload PDF files
   - PDFs will preview directly in browser

3. **Create landing page**:
   - Modern page with links to each PDF

**Pros**:
- ✅ Perfect SharePoint compatibility
- ✅ Browser preview works flawlessly
- ✅ Familiar format for users
- ✅ No JavaScript issues

**Cons**:
- ❌ Charts become static images
- ❌ No interactivity (hover, zoom)
- ❌ Need to regenerate for updates

---

## 🔧 Troubleshooting SharePoint Issues

### Issue: "This file can't be previewed"

**Cause**: HTML files can't be previewed in SharePoint by default

**Solutions**:
1. Rename file to `.aspx` extension (not recommended - security risk)
2. Add `?web=1` parameter to URL (may still be blocked)
3. Use download-based approach instead

### Issue: Charts don't render in embedded page

**Cause**: Content Security Policy (CSP) blocking JavaScript

**Check**:
```
Browser Console (F12) → Look for CSP errors
```

**Solutions**:
1. Use inline Chart.js (not CDN) - requires modifying HTML
2. Ask admin to whitelist CDN in Tenant Settings:
   ```
   SharePoint Admin Center → Settings → Scripting Capabilities →
   Custom Script → Allow users to run custom scripts
   ```
3. Use PDF approach instead

### Issue: Script Editor web part not available

**Cause**: Modern SharePoint site or admin disabled it

**Solutions**:
1. Switch to Classic site experience:
   ```
   Site Settings → Look and Feel → Classic SharePoint
   ```
2. Request admin enable Script Editor
3. Use embed web part with external hosting
4. Use PDF approach instead

---

## 📊 Creating a Puppeteer PDF Converter

Save as `convert_to_pdf.js`:

```javascript
const puppeteer = require('puppeteer');
const fs = require('fs').promises;

async function convertToPDF(htmlFile, outputPDF) {
    console.log(`Converting ${htmlFile} to ${outputPDF}...`);

    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    // Set viewport for better chart rendering
    await page.setViewport({ width: 1920, height: 1080 });

    // Load HTML file
    const htmlPath = `file://${process.cwd()}/${htmlFile}`;
    await page.goto(htmlPath, {
        waitUntil: 'networkidle0',
        timeout: 30000
    });

    // Wait for charts to render
    await page.waitForTimeout(3000);

    // Generate PDF
    await page.pdf({
        path: outputPDF,
        format: 'A4',
        landscape: true,
        printBackground: true,
        margin: {
            top: '20mm',
            right: '10mm',
            bottom: '20mm',
            left: '10mm'
        }
    });

    await browser.close();
    console.log(`✓ Created ${outputPDF}`);
}

// Convert all reports
async function convertAll() {
    const reports = [
        'cyber_november_comparison_2020_2025.html',
        'cyber_november_comparison_2024_2025.html',
        'cyber_november_comparison.html'
    ];

    for (const report of reports) {
        const pdfName = report.replace('.html', '.pdf');
        await convertToPDF(report, pdfName);
    }
}

convertAll().catch(console.error);
```

**Run**:
```bash
npm install puppeteer
node convert_to_pdf.js
```

---

## 🎯 Final Recommendation for SharePoint

Given SharePoint's limitations, here's the best approach:

### **For Interactive Reports**: Download-Based Distribution
1. Package as ZIP (use `./package_reports.sh`)
2. Upload ZIP to SharePoint document library
3. Add clear instructions for users
4. Users download → extract → view locally with full interactivity

### **For In-Browser Viewing**: PDF Approach
1. Convert HTML to PDF (use Puppeteer or wkhtmltopdf)
2. Upload PDFs to SharePoint
3. PDFs preview perfectly in SharePoint
4. Trade-off: No interactivity, but familiar format

### **For Best of Both Worlds**: Dual Distribution
1. Upload both ZIP (for interactive) and PDF (for quick preview)
2. Let users choose based on their needs:
   - Quick glance? → Open PDF in SharePoint
   - Deep analysis? → Download ZIP for interactive charts

---

## 💡 Alternative: Office 365 Static Web App

You mentioned potentially having access through Office 365. If you have **Microsoft 365 E3/E5**, you may have access to:

**Azure Static Web Apps** (included with some subscriptions):
- Check Azure Portal: portal.azure.com
- Look for "Static Web Apps" service
- If available, this is the BEST solution:
  - Direct URL access
  - Microsoft authentication built-in
  - No download needed
  - Full interactivity preserved

**To check access**:
1. Go to https://portal.azure.com
2. Sign in with your corporate account
3. Search for "Static Web Apps"
4. If you can create one, you have access!

Setup takes ~10 minutes and provides professional hosting with authentication.

---

## 📞 Need Help?

Common issues and solutions:
- Charts not rendering? → Check browser console (F12) for errors
- CSP errors? → Use PDF approach or request admin whitelist
- Download issues? → Check file size limits (SharePoint: 15GB, but smaller is better)
- Modern vs Classic? → Classic has better HTML support, Modern has better UX

For IT support requests, provide:
- SharePoint site URL
- Specific error messages (browser console)
- Browser version being used
