**Text Parsing and Slide Mapping**

The text-to-presentation app employs a sophisticated two-stage parsing approach. First, the ***build\_outline\_from\_text*** function in **outline.py:102** processes input text using either an LLM or fallback parsing. When an LLM is available, the system sends text to models like GPT-4 with a structured prompt requesting strict JSON output containing a title and slides array. Each slide includes a title, bullets, and optional speaker notes. The LLM intelligently identifies existing markdown headings and converts them to slide titles while condensing content into concise bullet points (max 12 words each).

  When no API key is provided, the ***\_fallback\_outline*** function in **outline.py:27** performs regex-based parsing, detecting markdown headers (**\#**) as slide titles and bullet points (**\-, \*, \+**) as slide content. It also splits long paragraphs at sentence boundaries to create digestible bullet points. The system calculates target slide count based on character length (roughly 800 characters per slide) to ensure appropriate presentation length.

  **Visual Style and Template Application**

  The ***build\_presentation\_from\_outline*** function in **slide\_builder.py:95** preserves the uploaded template's visual identity by leveraging PowerPoint's layout system. The ***\_pick\_layout*** function identifies "title and content" layouts from the template's slide masters, ensuring consistency with the original design. Instead of clearing template formatting, the ***\_set\_title*** and ***\_set\_bullets\_placeholder*** functions work with existing text frames and paragraphs, preserving fonts, colors, and styling.

  The system attempts to place content in template placeholders first, maintaining the template's visual hierarchy. When placeholders aren't available, it creates textboxes with standard positioning. The template\_assets.py module extracts images from slide masters for potential logo placement, though this feature is currently commented out. This approach ensures generated presentations maintain the professional appearance and branding of the original  
  template while adapting the content structure.  
