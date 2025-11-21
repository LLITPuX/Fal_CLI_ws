/**
 * Document Archiver Page - основна сторінка для архівування документів
 */

import { useState, useEffect, useRef } from 'react';
import { Upload, FileText, Save, Eye, Loader2, AlertCircle } from 'lucide-react';
import { CybersichHeader } from '../components/CybersichHeader';
import { NodeSchemaEditor } from '../components/archive/NodeSchemaEditor';
import { PromptEditor } from '../components/archive/PromptEditor';
import { Button } from '../components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ScrollArea } from '../components/ui/scroll-area';
import { archiveApi } from '../services/archive-api';
import type {
  DocumentType,
  NodeSchema,
  PromptTemplate,
  PreviewResponse,
  ArchiveResponse,
} from '../types/archive';

const backgroundImage = '/2d76d3ed895b0324df0b5302921cd6c50e5b7a9e.png';

export default function DocumentArchiverPage() {
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [selectedDocType, setSelectedDocType] = useState<DocumentType | null>(null);
  const [documentContent, setDocumentContent] = useState('');
  const [filePath, setFilePath] = useState('');
  const [currentSchema, setCurrentSchema] = useState<NodeSchema | null>(null);
  const [currentPrompt, setCurrentPrompt] = useState<PromptTemplate | null>(null);
  const [previewData, setPreviewData] = useState<PreviewResponse | null>(null);
  const [previewMode, setPreviewMode] = useState<'graph' | 'json'>('graph');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load document types on mount
  useEffect(() => {
    loadDocumentTypes();
  }, []);

  // Load schema and prompt when document type changes
  useEffect(() => {
    if (selectedDocType) {
      loadSchemaAndPrompt();
    }
  }, [selectedDocType]);

  const loadDocumentTypes = async () => {
    try {
      const response = await archiveApi.getDocumentTypes();
      setDocumentTypes(response.document_types);

      // Auto-select first type if available
      if (response.document_types.length > 0 && !selectedDocType) {
        setSelectedDocType(response.document_types[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Помилка завантаження типів документів');
    }
  };

  const loadSchemaAndPrompt = async () => {
    if (!selectedDocType) return;

    try {
      setIsLoading(true);
      setError(null);

      // Load Rule schema (default)
      const schema = await archiveApi.getSchemasForType(selectedDocType.id, 'Rule');
      setCurrentSchema(schema);

      // Load prompt
      const prompt = await archiveApi.getPrompt(selectedDocType.prompt_id);
      setCurrentPrompt(prompt);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Помилка завантаження схеми або промпту');
      console.error('Failed to load schema/prompt:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const content = await file.text();
      setDocumentContent(content);
      setFilePath(file.name);

      // Auto-detect document type from extension
      const extension = file.name.split('.').pop()?.toLowerCase();
      const matchingType = documentTypes.find(
        (dt) => dt.file_extension.replace('.', '') === extension
      );
      if (matchingType) {
        setSelectedDocType(matchingType);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Помилка читання файлу');
    }
  };

  const handlePasteContent = () => {
    navigator.clipboard
      .readText()
      .then((text) => {
        setDocumentContent(text);
        setFilePath('pasted-content.txt');
      })
      .catch(() => {
        setError('Не вдалося прочитати з буфера обміну');
      });
  };

  const handlePreview = async () => {
    if (!selectedDocType || !documentContent.trim()) {
      setError('Оберіть тип документа та введіть контент');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await archiveApi.previewArchive({
        content: documentContent,
        document_type: selectedDocType.id,
        schema_id: currentSchema?.id || null,
        prompt_id: currentPrompt?.id || null,
      });

      setPreviewData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Помилка preview');
      console.error('Preview failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleArchive = async () => {
    if (!selectedDocType || !documentContent.trim()) {
      setError('Оберіть тип документа та введіть контент');
      return;
    }

    if (!confirm('Ви впевнені, що хочете архівувати документ в FalkorDB?')) {
      return;
    }

    try {
      setIsSaving(true);
      setError(null);

      const response: ArchiveResponse = await archiveApi.archiveDocument({
        content: documentContent,
        file_path: filePath || 'unknown',
        document_type: selectedDocType.id,
        schema_id: currentSchema?.id || null,
        prompt_id: currentPrompt?.id || null,
      });

      alert(
        `Документ успішно архівовано!\n\n` +
          `Document ID: ${response.stats.document_id}\n` +
          `Rules: ${response.stats.rules_created}\n` +
          `Entities: ${response.stats.entities_created}\n` +
          `Relationships: ${response.stats.relationships_created}`
      );

      // Refresh preview
      await handlePreview();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Помилка архівування');
      console.error('Archive failed:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveSchema = async (schema: NodeSchema) => {
    if (!selectedDocType) return;

    try {
      await archiveApi.createSchemaVersion({
        schema_id: schema.id,
        schema,
      });
      setCurrentSchema(schema);
      alert('Схема збережена успішно!');
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Помилка збереження схеми');
    }
  };

  const handleSavePrompt = async (prompt: PromptTemplate) => {
    if (!selectedDocType) return;

    try {
      await archiveApi.createPromptVersion({
        prompt_id: prompt.id,
        prompt,
      });
      setCurrentPrompt(prompt);
      alert('Промпт збережено успішно!');
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Помилка збереження промпту');
    }
  };

  return (
    <div
      className="min-h-screen relative"
      style={{
        backgroundImage: `linear-gradient(rgba(243, 237, 220, 0.75), rgba(243, 237, 220, 0.75)), url(${backgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
    >
      <CybersichHeader title="Cybersich" subtitle="AI Помічник · Document Archiver" />

      <div className="max-w-7xl mx-auto h-[calc(100vh-80px)] flex flex-col gap-4 pt-4 px-4">
        {error && (
          <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 overflow-hidden min-h-0">
          {/* Left column: Document selection and content */}
          <div className="lg:col-span-1 flex flex-col gap-4 overflow-hidden">
            <Card className="flex-1 overflow-hidden flex flex-col">
              <CardHeader>
                <CardTitle>Документ</CardTitle>
                <CardDescription>Оберіть або вставте документ для архівування</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 overflow-hidden flex flex-col space-y-4">
                {/* Document type selector */}
                <div className="space-y-2">
                  <Label htmlFor="doc-type">Тип документа</Label>
                  <Select
                    value={selectedDocType?.id || ''}
                    onValueChange={(value) => {
                      const type = documentTypes.find((dt) => dt.id === value);
                      setSelectedDocType(type || null);
                    }}
                  >
                    <SelectTrigger id="doc-type">
                      <SelectValue placeholder="Оберіть тип..." />
                    </SelectTrigger>
                    <SelectContent>
                      {documentTypes.map((dt) => (
                        <SelectItem key={dt.id} value={dt.id}>
                          {dt.name} ({dt.file_extension})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* File upload */}
                <div className="space-y-2">
                  <Label>Завантаження файлу</Label>
                  <div className="flex gap-2">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".mdc,.md,.txt"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    <Button
                      variant="outline"
                      onClick={() => fileInputRef.current?.click()}
                      className="flex-1"
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      Вибрати файл
                    </Button>
                    <Button variant="outline" onClick={handlePasteContent}>
                      <FileText className="w-4 h-4 mr-2" />
                      Вставити
                    </Button>
                  </div>
                  {filePath && (
                    <p className="text-xs text-muted-foreground">Файл: {filePath}</p>
                  )}
                </div>

                {/* Document content */}
                <div className="space-y-2 flex-1 overflow-hidden flex flex-col">
                  <Label htmlFor="doc-content">Контент документа</Label>
                  <ScrollArea className="flex-1">
                    <Textarea
                      id="doc-content"
                      value={documentContent}
                      onChange={(e) => setDocumentContent(e.target.value)}
                      placeholder="Вставте або введіть контент документа..."
                      className="min-h-[300px] font-mono text-sm"
                    />
                  </ScrollArea>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Middle column: Schema and Prompt editors */}
          <div className="lg:col-span-1 flex flex-col gap-4 overflow-hidden">
            <Tabs defaultValue="schema" className="flex-1 overflow-hidden flex flex-col">
              <TabsList>
                <TabsTrigger value="schema">Схема вузла</TabsTrigger>
                <TabsTrigger value="prompt">Промпт</TabsTrigger>
              </TabsList>

              <TabsContent value="schema" className="flex-1 overflow-hidden">
                <ScrollArea className="h-full">
                  {isLoading ? (
                    <div className="flex items-center justify-center h-64">
                      <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                    </div>
                  ) : (
                    <NodeSchemaEditor
                      schema={currentSchema}
                      onSave={handleSaveSchema}
                      disabled={!selectedDocType || isLoading}
                    />
                  )}
                </ScrollArea>
              </TabsContent>

              <TabsContent value="prompt" className="flex-1 overflow-hidden">
                <ScrollArea className="h-full">
                  {isLoading ? (
                    <div className="flex items-center justify-center h-64">
                      <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                    </div>
                  ) : (
                    <PromptEditor
                      prompt={currentPrompt}
                      onSave={handleSavePrompt}
                      onPreview={(content) => {
                        console.log('Preview prompt:', content);
                      }}
                      disabled={!selectedDocType || isLoading}
                    />
                  )}
                </ScrollArea>
              </TabsContent>
            </Tabs>
          </div>

          {/* Right column: Preview */}
          <div className="lg:col-span-1 flex flex-col gap-4 overflow-hidden">
            <Card className="flex-1 overflow-hidden flex flex-col">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Preview</CardTitle>
                    <CardDescription>Попередній перегляд архівування</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handlePreview}
                      disabled={!selectedDocType || !documentContent.trim() || isLoading}
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      Preview
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleArchive}
                      disabled={
                        !selectedDocType ||
                        !documentContent.trim() ||
                        isLoading ||
                        isSaving
                      }
                    >
                      {isSaving ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Архівування...
                        </>
                      ) : (
                        <>
                          <Save className="w-4 h-4 mr-2" />
                          Архівувати
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="flex-1 overflow-hidden">
                {!previewData ? (
                  <div className="h-full flex items-center justify-center text-muted-foreground">
                    <div className="text-center">
                      <Eye className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>Натисніть "Preview" для попереднього перегляду</p>
                    </div>
                  </div>
                ) : (
                  <Tabs
                    value={previewMode}
                    onValueChange={(v) => setPreviewMode(v as 'graph' | 'json')}
                    className="h-full overflow-hidden flex flex-col"
                  >
                    <TabsList>
                      <TabsTrigger value="graph">Граф</TabsTrigger>
                      <TabsTrigger value="json">JSON</TabsTrigger>
                    </TabsList>

                    <TabsContent value="graph" className="flex-1 overflow-auto">
                      <div className="space-y-4">
                        <div>
                          <h4 className="font-semibold mb-2">Вузли ({previewData.nodes.length})</h4>
                          <div className="space-y-2">
                            {previewData.nodes.map((node, idx) => (
                              <Card key={idx} className="p-3">
                                <div className="font-mono text-sm">
                                  <span className="font-semibold text-primary">{node.label}</span>
                                  <div className="mt-2 text-xs text-muted-foreground">
                                    {Object.entries(node.properties)
                                      .slice(0, 5)
                                      .map(([key, value]) => (
                                        <div key={key}>
                                          {key}: {String(value).substring(0, 50)}
                                          {String(value).length > 50 ? '...' : ''}
                                        </div>
                                      ))}
                                  </div>
                                </div>
                              </Card>
                            ))}
                          </div>
                        </div>

                        <div>
                          <h4 className="font-semibold mb-2">
                            Зв'язки ({previewData.relationships.length})
                          </h4>
                          <div className="space-y-1">
                            {previewData.relationships.map((rel, idx) => (
                              <div key={idx} className="text-sm font-mono p-2 bg-muted rounded">
                                {rel.from_label} → {rel.relationship_type} → {rel.to_label}
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </TabsContent>

                    <TabsContent value="json" className="flex-1 overflow-auto">
                      <ScrollArea className="h-full">
                        <pre className="text-xs font-mono p-4 bg-muted rounded">
                          {JSON.stringify(previewData.json_preview, null, 2)}
                        </pre>
                      </ScrollArea>
                    </TabsContent>
                  </Tabs>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

