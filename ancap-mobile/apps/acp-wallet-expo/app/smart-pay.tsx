import * as Clipboard from "expo-clipboard";
import * as ImagePicker from "expo-image-picker";
import { CameraView, scanFromURLAsync, useCameraPermissions } from "expo-camera";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Linking,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import type {
  SmartPayCapabilities,
  SmartPayClientKnownRef,
  SmartPayExecution,
  SmartPayPaymentIntent,
  SmartPayQuote,
  SmartPayReceipt,
} from "@ancap/acp-api-client";
import { safeErrorMessage } from "@ancap/acp-wallet-sdk";
import { useLocalSearchParams } from "expo-router";
import { getApi, hasApiAuthHeader } from "@/lib/api";
import {
  clearSmartPayHistorySnapshots,
  loadSmartPayHistoryTimeline,
  mergeSmartPayActiveHistoryEntry,
  saveSmartPayHistoryEntry,
  type SmartPayHistoryEntry,
} from "@/lib/smart-pay-history";
import {
  buildSmartPayActiveHistoryEntry,
  buildSmartPayHistorySections,
  getSmartPayActiveExecutionTxRefs,
  getSmartPayActiveExecutionView,
  formatSmartPayTimestamp,
  formatSmartPayTxRefLabel,
  canSmartPayRefreshOrRecover,
  getSmartPayExecutionStatusLabel,
  getSmartPayHistoryAccessHint,
  getSmartPayHistoryAccessLabel,
  getSmartPayHistoryActionHint,
  getSmartPayHistoryActionLabel,
  getSmartPayHistoryRecoveryStateHint,
  getSmartPayHistoryRecoveryStateLabel,
  getSmartPayHistoryRestoreHint,
  getSmartPayHistoryAdditionalProofHint,
  getSmartPayHistoryAdditionalProofProvenanceHint,
  getSmartPayHistoryAdditionalProofProvenanceLabel,
  getSmartPayHistoryNextStepHint,
  getSmartPayHistoryNextStepLabel,
  getSmartPayHistoryAdditionalProofTxRefHint,
  getSmartPayHistoryProofTxRefHint,
  getSmartPayHistoryAdditionalProofTxRefs,
  getSmartPayHistoryAmountLabel,
  getSmartPayHistoryFreshnessHint,
  getSmartPayHistoryFreshnessLabel,
  getSmartPayHistoryRefreshButtonLabel,
  getSmartPayHistoryReceiptDisplay,
  getSmartPayHistoryMerchantHint,
  getSmartPayHistoryNetworkFeesHint,
  getSmartPayHistoryNetworkFeesLabel,
  getSmartPayHistoryPendingProofHint,
  getSmartPayHistoryProofEmptyStateHint,
  getSmartPayHistoryProofHint,
  getSmartPayHistoryProofLabel,
  getSmartPayHistoryRecoverButtonLabel,
  getSmartPayHistoryRecoveryInputHint,
  getSmartPayHistoryRecoveryInputLabel,
  getSmartPayHistoryProofProvenanceHint,
  getSmartPayHistoryProofProvenanceLabel,
  getSmartPayHistoryProofQualityHint,
  getSmartPayHistoryProofSyncHint,
  getSmartPayHistoryProofSyncLabel,
  getSmartPayHistoryProofQualityLabel,
  getSmartPayHistoryProofRouteDetailHint,
  getSmartPayHistoryProofRouteDetailLabel,
  getSmartPayHistoryProofRouteStepHint,
  getSmartPayHistoryProofRouteSteps,
  getSmartPayHistoryProofTxRefs,
  getSmartPayHistoryTxRefStorageHint,
  getSmartPayHistoryTxRefStorageLabel,
  getSmartPayHistoryExecutionProgressDisplayLines,
  getSmartPayHistoryOverviewLines,
  getSmartPayHistoryProgressHint,
  getSmartPayHistoryProgressSourceHint,
  getSmartPayHistoryProgressSourceLabel,
  getSmartPayHistorySnapshotStatusLabel,
  getSmartPayHistorySnapshotTitle,
  getSmartPayHistorySourceHint,
  getSmartPayHistorySourceLabel,
  getSmartPayRecoverHint,
  getSmartPayRefreshOrRecoverHint,
  canSmartPayRecoverExecution,
  resolveSmartPayExecutionSessionToken,
} from "@/lib/smart-pay-history-view";
import {
  getSmartPayQuoteExpiryHint,
  getSmartPayQuoteExpiryLabel,
  isSmartPayQuoteExpired,
} from "@/lib/smart-pay-quote";
import {
  canSmartPayRequestQuote,
  canSmartPayReviewQuote,
  getSmartPayIntentFreshnessWarning,
  getSmartPayQuoteFreshnessWarning,
  shouldInvalidateSmartPayParsedIntent,
  shouldInvalidateSmartPayQuote,
} from "@/lib/smart-pay-freshness";
import {
  clearSmartPaySession,
  loadSmartPaySession,
  saveSmartPaySession,
  type PersistedSmartPaySession,
  type SmartPayPayloadSource,
} from "@/lib/smart-pay-session";
import {
  canSubmitSmartPayRecoveryInput,
  formatSmartPayRecoveryRefPreview,
  getSmartPayRecoveryInputBlockReason,
  parseSmartPayRecoveryInput,
} from "@/lib/smart-pay-recovery";
import {
  deriveSmartPayExecuteSnapshotOrigin,
  deriveSmartPayLiveUpdateSnapshotOrigin,
  deriveSmartPaySnapshotOrigin,
} from "@/lib/smart-pay-snapshot-origin";
import {
  getSmartPaySharedDraft,
  shouldApplySmartPaySharedDraft,
} from "@/lib/smart-pay-share";

export default function SmartPayScreen() {
  const sharedParams = useLocalSearchParams<{
    rawPayload?: string | string[];
    payload?: string | string[];
    selectedAsset?: string | string[];
    asset?: string | string[];
  }>();
  const lastAppliedSharedDraftRef = useRef<string | null>(null);
  const [capabilities, setCapabilities] = useState<SmartPayCapabilities | null>(null);
  const [rawPayload, setRawPayload] = useState("");
  const [payloadSource, setPayloadSource] = useState<SmartPayPayloadSource>("paste");
  const [selectedAsset, setSelectedAsset] = useState("ACP");
  const [loadingCapabilities, setLoadingCapabilities] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [intent, setIntent] = useState<SmartPayPaymentIntent | null>(null);
  const [quote, setQuote] = useState<SmartPayQuote | null>(null);
  const [execution, setExecution] = useState<SmartPayExecution | null>(null);
  const [receipt, setReceipt] = useState<SmartPayReceipt | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [snapshotOrigin, setSnapshotOrigin] = useState<SmartPayHistoryEntry["snapshotOrigin"]>("local");
  const [recoveryDraftTxs, setRecoveryDraftTxs] = useState("");
  const [cameraPermission, requestCameraPermission] = useCameraPermissions();
  const [showCamera, setShowCamera] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [confirmationAccepted, setConfirmationAccepted] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [history, setHistory] = useState<SmartPayHistoryEntry[]>([]);

  const loadHistoryTimeline = async (limit = 8): Promise<SmartPayHistoryEntry[]> => {
    return loadSmartPayHistoryTimeline({
      hasAccountAuth,
      limit,
      listRemoteHistory: async (remoteLimit) => {
        const remote = await getApi().listSmartPayPayments(remoteLimit);
        return remote.payments;
      },
    });
  };

  const buildCurrentPersistedSession = (
    overrides: Partial<PersistedSmartPaySession> = {}
  ): Omit<PersistedSmartPaySession, "version" | "savedAt"> => ({
    rawPayload,
    payloadSource,
    selectedAsset,
    intent,
    quote,
    execution,
    receipt,
    sessionToken,
    snapshotOrigin: snapshotOrigin ?? "local",
    recoveryDraftTxs,
    ...overrides,
  });

  const supportedSymbols = useMemo(() => {
    const fromApi = capabilities?.supportedAssets?.map((item) => item.symbol).filter(Boolean) ?? [];
    const uniq = Array.from(new Set(fromApi));
    return uniq.length > 0 ? uniq : ["ACP", "wACP", "USDT"];
  }, [capabilities]);

  const hasAccountAuth = useMemo(() => hasApiAuthHeader(), []);
  const historySections = useMemo(() => buildSmartPayHistorySections(history), [history]);
  const historyOverviewLines = useMemo(
    () => getSmartPayHistoryOverviewLines(history, { hasAccountAuth }),
    [history, hasAccountAuth]
  );
  const quoteExpired = useMemo(() => (quote ? isSmartPayQuoteExpired(quote) : false), [quote]);
  const sharedDraft = useMemo(
    () => getSmartPaySharedDraft(sharedParams),
    [sharedParams.asset, sharedParams.payload, sharedParams.rawPayload, sharedParams.selectedAsset]
  );
  const intentFreshnessWarning = useMemo(
    () => getSmartPayIntentFreshnessWarning(intent, rawPayload),
    [intent, rawPayload]
  );
  const quoteFreshnessWarning = useMemo(
    () =>
      getSmartPayQuoteFreshnessWarning({
        intent,
        quote,
        rawPayload,
        selectedAsset,
      }),
    [intent, quote, rawPayload, selectedAsset]
  );
  const shouldResetParsedIntent = useMemo(
    () => shouldInvalidateSmartPayParsedIntent(intent, rawPayload),
    [intent, rawPayload]
  );
  const shouldResetQuote = useMemo(
    () =>
      shouldInvalidateSmartPayQuote({
        intent,
        quote,
        rawPayload,
        selectedAsset,
      }),
    [intent, quote, rawPayload, selectedAsset]
  );
  const canRequestQuote = useMemo(
    () => canSmartPayRequestQuote(intent, rawPayload),
    [intent, rawPayload]
  );
  const canReviewQuote = useMemo(
    () =>
      canSmartPayReviewQuote({
        intent,
        quote,
        rawPayload,
        selectedAsset,
      }),
    [intent, quote, rawPayload, selectedAsset]
  );

  useEffect(() => {
    void (async () => {
      try {
        const [result, persisted, persistedHistory] = await Promise.all([
          getApi().getSmartPayCapabilities(),
          loadSmartPaySession(),
          loadHistoryTimeline(),
        ]);
        setCapabilities(result);
        setHistory(persistedHistory);
        if (persisted) {
          setRawPayload(persisted.rawPayload || "");
          setPayloadSource(persisted.payloadSource || "paste");
          setSelectedAsset(persisted.selectedAsset || "ACP");
          setIntent(persisted.intent ?? null);
          setQuote(persisted.quote ?? null);
          setExecution(persisted.execution ?? null);
          setReceipt(persisted.receipt ?? null);
          setSessionToken(persisted.sessionToken ?? null);
          setSnapshotOrigin(persisted.snapshotOrigin ?? "local");
          setRecoveryDraftTxs(persisted.recoveryDraftTxs ?? "");
          setShowConfirmation(false);
          setConfirmationAccepted(false);
        }
      } catch (e) {
        setError(safeErrorMessage(e, "Failed to load Smart Pay capabilities"));
      } finally {
        setLoadingCapabilities(false);
        setHydrated(true);
      }
    })();
  }, []);

  useEffect(() => {
    if (!supportedSymbols.includes(selectedAsset)) {
      setSelectedAsset(supportedSymbols[0] ?? "ACP");
    }
  }, [selectedAsset, supportedSymbols]);

  useEffect(() => {
    if (!hydrated || !sharedDraft) {
      return;
    }

    const alreadyApplied = lastAppliedSharedDraftRef.current === sharedDraft.dedupeKey;
    const shouldApply = shouldApplySmartPaySharedDraft(sharedDraft, {
      rawPayload,
      payloadSource,
      selectedAsset,
    });
    if (alreadyApplied && !shouldApply) {
      return;
    }
    if (!shouldApply) {
      return;
    }

    lastAppliedSharedDraftRef.current = sharedDraft.dedupeKey;
    setRawPayload(sharedDraft.rawPayload);
    setPayloadSource("share");
    if (sharedDraft.selectedAsset) {
      setSelectedAsset(sharedDraft.selectedAsset);
    }
    setIntent(null);
    setQuote(null);
    setExecution(null);
    setReceipt(null);
    setSessionToken(null);
    setSnapshotOrigin("local");
    setRecoveryDraftTxs("");
    setShowConfirmation(false);
    setConfirmationAccepted(false);
    setError("");
  }, [hydrated, sharedDraft, sharedParams]);

  useEffect(() => {
    if (!hydrated) return;
    void saveSmartPaySession(buildCurrentPersistedSession());
  }, [hydrated, rawPayload, payloadSource, selectedAsset, intent, quote, execution, receipt, sessionToken, snapshotOrigin, recoveryDraftTxs]);

  useEffect(() => {
    if (!hydrated || !shouldResetQuote || !quote) {
      return;
    }

    setQuote(null);
    setExecution(null);
    setReceipt(null);
    setSessionToken(null);
    setSnapshotOrigin("local");
    setRecoveryDraftTxs("");
    setShowConfirmation(false);
    setConfirmationAccepted(false);
  }, [hydrated, quote, shouldResetQuote]);

  useEffect(() => {
    if (!hydrated || !shouldResetParsedIntent || !intent) {
      return;
    }

    setIntent(null);
    setQuote(null);
    setExecution(null);
    setReceipt(null);
    setSessionToken(null);
    setSnapshotOrigin("local");
    setRecoveryDraftTxs("");
    setShowConfirmation(false);
    setConfirmationAccepted(false);
  }, [hydrated, intent, shouldResetParsedIntent]);

  const onPaste = async () => {
    const text = await Clipboard.getStringAsync();
    if (text?.trim()) {
      setPayloadSource("paste");
      setRawPayload(text.trim());
    }
  };

  const onOpenCamera = async () => {
    if (!cameraPermission?.granted) {
      const res = await requestCameraPermission();
      if (!res.granted) {
        Alert.alert("Smart Pay", "Camera permission is required to scan QR codes.");
        return;
      }
    }
    setShowCamera(true);
  };

  const onPickFromGallery = async () => {
    try {
      setBusy(true);
      setError("");
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) {
        Alert.alert("Smart Pay", "Photo library permission is required to import QR images.");
        return;
      }
      const picked = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ["images"],
        allowsEditing: false,
        quality: 1,
      });
      if (picked.canceled || !picked.assets?.length) return;
      const asset = picked.assets[0];
      if (!asset?.uri) throw new Error("Selected image has no URI");
      const scans = await scanFromURLAsync(asset.uri, ["qr"]);
      const first = scans.find((item) => typeof item.data === "string" && item.data.trim());
      if (!first?.data) {
        Alert.alert(
          "Smart Pay",
          "No QR code found in selected image. Paste receipt/invoice OCR text instead?",
          [
            { text: "Cancel", style: "cancel" },
            {
              text: "Paste OCR text",
              onPress: async () => {
                const text = await Clipboard.getStringAsync();
                if (text?.trim()) {
                  setPayloadSource("ocr");
                  setRawPayload(text.trim());
                }
              },
            },
          ],
        );
        return;
      }
      setPayloadSource("photo");
      setRawPayload(first.data.trim());
    } catch (e) {
      setError(safeErrorMessage(e, "Gallery import failed"));
    } finally {
      setBusy(false);
    }
  };

  const onCameraScanned = ({ data }: { data: string }) => {
    const value = (data || "").trim();
    if (!value) return;
    setPayloadSource("camera");
    setRawPayload(value);
    setShowCamera(false);
  };

  const onResetConfirmation = () => {
    setShowConfirmation(false);
    setConfirmationAccepted(false);
    setExecution(null);
    setReceipt(null);
    setSessionToken(null);
    setSnapshotOrigin("local");
    setRecoveryDraftTxs("");
  };

  const onClearSession = async () => {
    setRawPayload("");
    setPayloadSource("paste");
    setSelectedAsset(supportedSymbols[0] ?? "ACP");
    setIntent(null);
    setQuote(null);
    setExecution(null);
    setReceipt(null);
    setSessionToken(null);
    setSnapshotOrigin("local");
    setRecoveryDraftTxs("");
    setShowConfirmation(false);
    setConfirmationAccepted(false);
    setError("");
    await clearSmartPaySession();
  };

  const onClearHistory = async () => {
    setBusy(true);
    setError("");
    try {
      const nextHistory = await clearSmartPayHistorySnapshots({
        hasAccountAuth,
        listRemoteHistory: async (limit) => {
          const remote = await getApi().listSmartPayPayments(limit);
          return remote.payments;
        },
      });
      setHistory(nextHistory);
    } catch (e) {
      setError(safeErrorMessage(e, "Failed to clear local Smart Pay history"));
    } finally {
      setBusy(false);
    }
  };

  const onResumeHistoryEntry = (entry: SmartPayHistoryEntry) => {
    setRawPayload(entry.intent.rawPayload || "");
    setPayloadSource(entry.intent.source);
    setSelectedAsset(entry.quote?.sourceAsset.symbol || entry.intent.asset.symbol || "ACP");
    setIntent(entry.intent);
    setQuote(entry.quote ?? null);
    setExecution(entry.execution);
    setReceipt(entry.receipt ?? null);
    setSessionToken(entry.sessionToken ?? null);
    setSnapshotOrigin(
      deriveSmartPaySnapshotOrigin({
        hasAccountAuth,
        sessionToken: entry.sessionToken,
        previousOrigin: entry.snapshotOrigin ?? null,
      })
    );
    setRecoveryDraftTxs("");
    setShowConfirmation(false);
    setConfirmationAccepted(false);
    setError("");
  };

  const parsedRecoveryInput = useMemo(() => parseSmartPayRecoveryInput(recoveryDraftTxs), [recoveryDraftTxs]);
  const parsedRecoveryTxs = parsedRecoveryInput.txids;
  const recoveryInputBlockReason = useMemo(
    () => getSmartPayRecoveryInputBlockReason(recoveryDraftTxs),
    [recoveryDraftTxs]
  );
  const canSubmitRecoveryInput = useMemo(
    () => canSubmitSmartPayRecoveryInput(recoveryDraftTxs),
    [recoveryDraftTxs]
  );
  const activeHistoryEntry = useMemo<SmartPayHistoryEntry | null>(() => {
    const current = buildSmartPayActiveHistoryEntry({
      snapshotSavedAt: execution?.updatedAt ?? null,
      intent,
      quote,
      execution,
      receipt,
      sessionToken,
      snapshotOrigin,
    });

    if (!current) {
      return null;
    }

    const matchingHistoryEntry = history.find((entry) => entry.id === current.id) ?? null;
    return mergeSmartPayActiveHistoryEntry(matchingHistoryEntry, current);
  }, [execution, history, intent, quote, receipt, sessionToken, snapshotOrigin]);
  const activeExecutionView = getSmartPayActiveExecutionView(activeHistoryEntry, execution);
  const activeSessionToken = useMemo(
    () => resolveSmartPayExecutionSessionToken(activeHistoryEntry, sessionToken),
    [activeHistoryEntry, sessionToken]
  );
  const canRefreshExecution = Boolean(
    activeExecutionView &&
      canSmartPayRefreshOrRecover({
        sessionToken: activeSessionToken,
        hasAccountAuth,
      })
  );
  const canRecoverExecution = Boolean(
    activeExecutionView &&
      canSmartPayRecoverExecution({
        sessionToken: activeSessionToken,
        hasAccountAuth,
        recoverable: activeExecutionView.recoverable,
      })
  );
  const activeExecutionTxRefs = useMemo(
    () => getSmartPayActiveExecutionTxRefs(activeHistoryEntry, execution),
    [activeHistoryEntry, execution]
  );
  const activeExecutionProgressDisplayLines = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryExecutionProgressDisplayLines(activeHistoryEntry) : []),
    [activeHistoryEntry]
  );
  const activeProgressHint = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryProgressHint(activeHistoryEntry) : null),
    [activeHistoryEntry]
  );
  const activeProgressSourceLabel = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryProgressSourceLabel(activeHistoryEntry) : null),
    [activeHistoryEntry]
  );
  const activeProgressSourceHint = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryProgressSourceHint(activeHistoryEntry) : null),
    [activeHistoryEntry]
  );
  const activePendingProofHint = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryPendingProofHint(activeHistoryEntry) : null),
    [activeHistoryEntry]
  );
  const activeProofRouteDetailLabel = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryProofRouteDetailLabel(activeHistoryEntry) : null),
    [activeHistoryEntry]
  );
  const activeProofRouteDetailHint = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryProofRouteDetailHint(activeHistoryEntry) : null),
    [activeHistoryEntry]
  );
  const activeProofQualityLabel = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryProofQualityLabel(activeHistoryEntry) : null),
    [activeHistoryEntry]
  );
  const activeProofQualityHint = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryProofQualityHint(activeHistoryEntry) : null),
    [activeHistoryEntry]
  );
  const activeProofProvenanceLabel = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryProofProvenanceLabel(activeHistoryEntry) : null),
    [activeHistoryEntry]
  );
  const activeProofProvenanceHint = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryProofProvenanceHint(activeHistoryEntry) : null),
    [activeHistoryEntry]
  );
  const activeLinkedProofTxRefs = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryProofTxRefs(activeHistoryEntry) : []),
    [activeHistoryEntry]
  );
  const activeProofRouteSteps = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryProofRouteSteps(activeHistoryEntry) : []),
    [activeHistoryEntry]
  );
  const activeAdditionalProofTxRefs = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryAdditionalProofTxRefs(activeHistoryEntry) : []),
    [activeHistoryEntry]
  );
  const activeAdditionalProofHint = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryAdditionalProofHint(activeHistoryEntry) : null),
    [activeHistoryEntry]
  );
  const activeAdditionalProofProvenanceLabel = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryAdditionalProofProvenanceLabel(activeHistoryEntry) : null),
    [activeHistoryEntry]
  );
  const activeAdditionalProofProvenanceHint = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryAdditionalProofProvenanceHint(activeHistoryEntry) : null),
    [activeHistoryEntry]
  );
  const activeReceiptDisplay = useMemo(
    () => (activeHistoryEntry ? getSmartPayHistoryReceiptDisplay(activeHistoryEntry) : null),
    [activeHistoryEntry]
  );

  const onOpenConfirmation = () => {
    if (!intent || !quote) {
      Alert.alert("Smart Pay", "Get a quote first.");
      return;
    }
    if (quoteFreshnessWarning) {
      Alert.alert("Smart Pay", quoteFreshnessWarning);
      return;
    }
    if (isSmartPayQuoteExpired(quote)) {
      Alert.alert("Smart Pay", "This quote expired. Get a fresh quote before reviewing or executing payment.");
      return;
    }
    setShowConfirmation(true);
    setConfirmationAccepted(false);
    setExecution(null);
    setReceipt(null);
    setSessionToken(null);
    setSnapshotOrigin("local");
    setRecoveryDraftTxs("");
  };

  const onOpenExplorerUrl = async (url: string | null | undefined) => {
    if (!url) return;
    try {
      await Linking.openURL(url);
    } catch (e) {
      setError(safeErrorMessage(e, "Failed to open explorer link"));
    }
  };

  const onParse = async () => {
    if (!rawPayload.trim()) {
      Alert.alert("Smart Pay", "Paste or enter a QR payload first.");
      return;
    }
    setBusy(true);
    setError("");
    setQuote(null);
    setExecution(null);
    setReceipt(null);
    setSessionToken(null);
    setSnapshotOrigin("local");
    setRecoveryDraftTxs("");
    setShowConfirmation(false);
    setConfirmationAccepted(false);
    try {
      const result = await getApi().parseSmartQr({
        source: payloadSource,
        rawPayload: rawPayload.trim(),
      });
      setIntent(result.paymentIntent);
    } catch (e) {
      setIntent(null);
      setError(safeErrorMessage(e, "Parse failed"));
    } finally {
      setBusy(false);
    }
  };

  const onQuote = async () => {
    if (!intent) {
      Alert.alert("Smart Pay", "Parse a payment intent first.");
      return;
    }
    if (intentFreshnessWarning) {
      Alert.alert("Smart Pay", intentFreshnessWarning);
      return;
    }
    setBusy(true);
    setError("");
    setExecution(null);
    setReceipt(null);
    setSessionToken(null);
    setSnapshotOrigin("local");
    setRecoveryDraftTxs("");
    setShowConfirmation(false);
    setConfirmationAccepted(false);
    try {
      const result = await getApi().quoteSmartPay({
        paymentIntentId: intent.id,
        sourcePreference: {
          preferredAsset: selectedAsset,
          allowedAssets: supportedSymbols,
          maxSlippageBps: 150,
          minAcpFeeReserve: capabilities?.minAcpFeeReserve ?? "1.0",
        },
      });
      setQuote(result.quote);
    } catch (e) {
      setQuote(null);
      setError(safeErrorMessage(e, "Quote failed"));
    } finally {
      setBusy(false);
    }
  };

  const onExecute = async () => {
    if (!intent || !quote) {
      Alert.alert("Smart Pay", "Get a quote first.");
      return;
    }
    if (!showConfirmation || !confirmationAccepted) {
      Alert.alert("Smart Pay", "Review and explicitly accept payment details before execute.");
      return;
    }
    if (quoteFreshnessWarning) {
      Alert.alert("Smart Pay", quoteFreshnessWarning);
      return;
    }
    if (isSmartPayQuoteExpired(quote)) {
      Alert.alert("Smart Pay", "This quote expired. Get a fresh quote before executing payment.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const result = await getApi().executeSmartPay({
        paymentIntentId: intent.id,
        quoteId: quote.quoteId,
        confirmationAccepted,
        deviceContext: {
          platform: Platform.OS === "ios" ? "ios" : "android",
          appVersion: null,
        },
      });
      const nextSessionToken = result.sessionToken ?? null;
      const receiptResult = await getApi().getSmartPayReceipt(result.execution.id, nextSessionToken);
      const nextSnapshotOrigin = deriveSmartPayExecuteSnapshotOrigin({
        hasAccountAuth,
        nextSessionToken,
        currentOrigin: snapshotOrigin ?? null,
      });
      setExecution(result.execution);
      setReceipt(receiptResult);
      setSessionToken(nextSessionToken);
      setSnapshotOrigin(nextSnapshotOrigin);
      await saveSmartPayHistoryEntry({
        id: result.execution.id,
        savedAt: new Date().toISOString(),
        intent,
        quote,
        execution: result.execution,
        receipt: receiptResult,
        sessionToken: nextSessionToken,
        snapshotOrigin: nextSnapshotOrigin,
      });
      setHistory(await loadHistoryTimeline());
      setShowConfirmation(false);
      setConfirmationAccepted(false);

      // SQ-7 remains awaiting_local_signature. Do not automatically submit a
      // server-provided plan before reviewed payload binding and durable recovery
      // are wired into this screen. Existing receipt/recovery UI stays available.

    } catch (e) {
      setError(safeErrorMessage(e, "Execute failed"));
    } finally {
      setBusy(false);
    }
  };

  const onRefreshExecution = async () => {
    if (!execution) return;
    setBusy(true);
    setError("");
    try {
      const requestSessionToken = resolveSmartPayExecutionSessionToken(activeHistoryEntry, sessionToken);
      const [result, receiptResult] = await Promise.all([
        getApi().getSmartPayExecution(execution.id, requestSessionToken),
        getApi().getSmartPayReceipt(execution.id, requestSessionToken),
      ]);
      setExecution(result.execution);
      setReceipt(receiptResult);
      const nextSessionToken = result.sessionToken ?? requestSessionToken ?? null;
      const nextSnapshotOrigin = deriveSmartPayLiveUpdateSnapshotOrigin({
        hasAccountAuth,
        requestSessionToken,
        nextSessionToken,
        currentOrigin: snapshotOrigin ?? null,
        activeHistoryOrigin: activeHistoryEntry?.snapshotOrigin ?? null,
      });
      setSessionToken(nextSessionToken);
      setSnapshotOrigin(nextSnapshotOrigin);
      if (intent) {
        await saveSmartPayHistoryEntry({
          id: result.execution.id,
          savedAt: new Date().toISOString(),
          intent,
          quote,
          execution: result.execution,
          receipt: receiptResult,
          sessionToken: nextSessionToken,
          snapshotOrigin: nextSnapshotOrigin,
        });
        setHistory(await loadHistoryTimeline());
      }
    } catch (e) {
      setError(safeErrorMessage(e, "Refresh failed"));
    } finally {
      setBusy(false);
    }
  };

  const onRecover = async () => {
    if (!execution) return;

    const clientKnownTxs = parsedRecoveryTxs;
    const clientKnownRefs: SmartPayClientKnownRef[] = parsedRecoveryInput.refs.map((ref) => ({
      txid: ref.txid,
      network: ref.network,
      explorerUrl: ref.explorerUrl,
    }));
    if (!canSubmitRecoveryInput) {
      Alert.alert(
        "Smart Pay",
        recoveryInputBlockReason ??
          "No valid tx hash or explorer link was parsed from this recovery input. Fix the pasted values or clear the field to run a status-only recovery pass."
      );
      return;
    }

    setBusy(true);
    setError("");
    try {
      const requestSessionToken = resolveSmartPayExecutionSessionToken(activeHistoryEntry, sessionToken);
      const result = await getApi().recoverSmartPay(
        execution.id,
        { clientKnownTxs, clientKnownRefs },
        requestSessionToken
      );
      const nextSessionToken = result.sessionToken ?? requestSessionToken ?? null;
      const receiptResult = await getApi().getSmartPayReceipt(execution.id, nextSessionToken);
      const nextSnapshotOrigin = deriveSmartPayLiveUpdateSnapshotOrigin({
        hasAccountAuth,
        requestSessionToken,
        nextSessionToken,
        currentOrigin: snapshotOrigin ?? null,
        activeHistoryOrigin: activeHistoryEntry?.snapshotOrigin ?? null,
      });
      setExecution(result.execution);
      setReceipt(receiptResult);
      setSessionToken(nextSessionToken);
      setSnapshotOrigin(nextSnapshotOrigin);
      setRecoveryDraftTxs("");
      if (intent) {
        await saveSmartPayHistoryEntry({
          id: result.execution.id,
          savedAt: new Date().toISOString(),
          intent,
          quote,
          execution: result.execution,
          receipt: receiptResult,
          sessionToken: nextSessionToken,
          snapshotOrigin: nextSnapshotOrigin,
        });
        setHistory(await loadHistoryTimeline());
      }
    } catch (e) {
      setError(safeErrorMessage(e, "Recover failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Smart Pay beta</Text>
      <Text style={styles.subtitle}>
        Smart QR flow beta: paste/share payload → parse → quote → execute → refresh/recover, with stored session history and receipt snapshots.
      </Text>
      <View style={styles.topActions}>
        <Pressable style={styles.secondary} onPress={onClearSession} disabled={busy}>
          <Text style={styles.secondaryText}>Reset session</Text>
        </Pressable>
      </View>

      {history.length ? (
        <View style={styles.card}>
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.label}>Recent Smart Pay sessions</Text>
            <Pressable onPress={onClearHistory} disabled={busy}>
              <Text style={styles.inlineAction}>Clear history</Text>
            </Pressable>
          </View>
          <Text style={styles.meta}>Secure device-local snapshots merged with authenticated backend payment history when available. Clearing history removes only the local secure-store snapshots on this device; signed-in backend payment history remains server-side and will still reappear here when account-authenticated history is enabled.</Text>
          <Text style={styles.meta}>Entries without the original session token may still refresh/recover after account sign-in, but anonymous live resume remains unavailable on this device.</Text>
          {historyOverviewLines.length ? (
            <View style={styles.historyOverviewCard}>
              <Text style={styles.historyOverviewTitle}>History overview</Text>
              {historyOverviewLines.map((line) => (
                <Text key={`history-overview-${line}`} style={styles.meta}>{line}</Text>
              ))}
            </View>
          ) : null}
          {!hasAccountAuth ? (
            <Text style={styles.inlineHint}>Account-authenticated backend history is currently disabled in this Expo build. Set EXPO_PUBLIC_ANCAP_API_AUTH_HEADER to enable authenticated payment history/resume for the same ANCAP account.</Text>
          ) : null}
          {historySections.map((section) => (
            <View key={section.key} style={styles.historySection}>
              <Text style={styles.historySectionTitle}>{section.title}</Text>
              {section.entries.map((entry) => {
                const pendingProofHint = getSmartPayHistoryPendingProofHint(entry);
                const proofRouteDetailLabel = getSmartPayHistoryProofRouteDetailLabel(entry);
                const proofRouteDetailHint = getSmartPayHistoryProofRouteDetailHint(entry);
                const proofQualityLabel = getSmartPayHistoryProofQualityLabel(entry);
                const proofQualityHint = getSmartPayHistoryProofQualityHint(entry);
                const proofProvenanceLabel = getSmartPayHistoryProofProvenanceLabel(entry);
                const proofProvenanceHint = getSmartPayHistoryProofProvenanceHint(entry);
                const additionalProofHint = getSmartPayHistoryAdditionalProofHint(entry);
                const additionalProofProvenanceLabel = getSmartPayHistoryAdditionalProofProvenanceLabel(entry);
                const additionalProofProvenanceHint = getSmartPayHistoryAdditionalProofProvenanceHint(entry);
                const receiptDisplay = getSmartPayHistoryReceiptDisplay(entry);
                const merchantHint = getSmartPayHistoryMerchantHint(receiptDisplay);
                const progressDisplayLines = getSmartPayHistoryExecutionProgressDisplayLines(entry);
                const progressSourceLabel = getSmartPayHistoryProgressSourceLabel(entry);
                const progressSourceHint = getSmartPayHistoryProgressSourceHint(entry);

                return (
                  <Pressable
                    key={entry.id}
                    style={styles.historyItem}
                    onPress={() => onResumeHistoryEntry(entry)}
                  >
                    <View style={styles.historyRow}>
                      <Text style={styles.historyTitle}>
                        {getSmartPayHistoryAmountLabel(entry)}
                      </Text>
                      <View style={[styles.statusBadge, section.key === "completed" ? styles.statusBadgeCompleted : section.key === "needs_attention" ? styles.statusBadgeAttention : styles.statusBadgeInFlight]}>
                        <Text style={styles.statusBadgeText}>{getSmartPayExecutionStatusLabel(entry.execution.status)}</Text>
                      </View>
                    </View>
                    <Text style={styles.meta}>Recipient: {entry.receipt?.recipientAddress ?? entry.intent.recipient.address}</Text>
                    {receiptDisplay.merchantLabel ? (
                      <Text style={styles.meta}>Merchant: {receiptDisplay.merchantLabel}</Text>
                    ) : null}
                    {receiptDisplay.merchantCategory ? (
                      <Text style={styles.meta}>Merchant category: {receiptDisplay.merchantCategory}</Text>
                    ) : null}
                    {receiptDisplay.merchantInvoiceId ? (
                      <Text style={styles.meta}>Invoice: {receiptDisplay.merchantInvoiceId}</Text>
                    ) : null}
                    {receiptDisplay.merchantWebsite ? (
                      <Pressable onPress={() => void onOpenExplorerUrl(receiptDisplay.merchantWebsite)}>
                        <Text style={styles.inlineAction}>{receiptDisplay.merchantWebsite}</Text>
                      </Pressable>
                    ) : null}
                    {merchantHint ? (
                      <Text style={styles.inlineHint}>{merchantHint}</Text>
                    ) : null}
                    <Text style={styles.meta}>Execution: {entry.execution.id}</Text>
                    <Text style={styles.meta}>History source: {getSmartPayHistorySourceLabel(entry)}</Text>
                    <Text style={styles.meta}>{getSmartPayHistorySourceHint(entry)}</Text>
                    <Text style={styles.meta}>{getSmartPayHistoryFreshnessLabel(entry)}</Text>
                    <Text style={styles.meta}>{getSmartPayHistoryFreshnessHint(entry, { hasAccountAuth })}</Text>
                    <Text style={styles.meta}>Resume access: {getSmartPayHistoryAccessLabel(entry, { hasAccountAuth })}</Text>
                    <Text style={styles.meta}>Recovery state: {getSmartPayHistoryRecoveryStateLabel(entry, { hasAccountAuth }).replace(/^Recovery state: /, "")}</Text>
                    <Text style={styles.meta}>Available actions: {getSmartPayHistoryActionLabel(entry, { hasAccountAuth })}</Text>
                    <Text style={styles.meta}>{getSmartPayHistoryNextStepLabel(entry, { hasAccountAuth })}</Text>
                    {progressDisplayLines.length ? (
                      progressDisplayLines.map((line) => (
                        <Text key={`history-progress-${entry.id}-${line}`} style={styles.meta}>{line}</Text>
                      ))
                    ) : null}
                    {getSmartPayHistoryProgressHint(entry) ? (
                      <Text style={styles.meta}>{getSmartPayHistoryProgressHint(entry)}</Text>
                    ) : null}
                    <Text style={styles.meta}>{progressSourceLabel}</Text>
                    <Text style={styles.inlineHint}>{progressSourceHint}</Text>
                    <Text style={styles.meta}>{getSmartPayHistoryProofLabel(entry)}</Text>
                    <Text style={styles.meta}>{getSmartPayHistoryProofHint(entry, { hasAccountAuth })}</Text>
                    <Text style={styles.meta}>{getSmartPayHistoryProofSyncLabel(entry, { hasAccountAuth })}</Text>
                    <Text style={styles.inlineHint}>{getSmartPayHistoryProofSyncHint(entry, { hasAccountAuth })}</Text>
                    {proofRouteDetailLabel ? (
                      <Text style={styles.meta}>{proofRouteDetailLabel}</Text>
                    ) : null}
                    {proofRouteDetailHint ? (
                      <Text style={styles.inlineHint}>{proofRouteDetailHint}</Text>
                    ) : null}
                    {proofQualityLabel ? (
                      <Text style={styles.meta}>{proofQualityLabel}</Text>
                    ) : null}
                    {proofQualityHint ? (
                      <Text style={styles.inlineHint}>{proofQualityHint}</Text>
                    ) : null}
                    {proofProvenanceLabel ? (
                      <Text style={styles.meta}>{proofProvenanceLabel}</Text>
                    ) : null}
                    {proofProvenanceHint ? (
                      <Text style={styles.inlineHint}>{proofProvenanceHint}</Text>
                    ) : null}
                    {pendingProofHint ? (
                      <Text style={styles.inlineHint}>{pendingProofHint}</Text>
                    ) : null}
                    {additionalProofHint ? (
                      <Text style={styles.inlineHint}>{additionalProofHint}</Text>
                    ) : null}
                    {additionalProofProvenanceLabel ? (
                      <Text style={styles.meta}>{additionalProofProvenanceLabel}</Text>
                    ) : null}
                    {additionalProofProvenanceHint ? (
                      <Text style={styles.inlineHint}>{additionalProofProvenanceHint}</Text>
                    ) : null}
                    <Text style={styles.meta}>{getSmartPayHistoryAccessHint(entry, { hasAccountAuth })}</Text>
                    <Text style={styles.meta}>{getSmartPayHistoryRecoveryStateHint(entry, { hasAccountAuth })}</Text>
                    <Text style={styles.meta}>{getSmartPayHistoryActionHint(entry, { hasAccountAuth })}</Text>
                    <Text style={styles.meta}>{getSmartPayHistoryNextStepHint(entry, { hasAccountAuth })}</Text>
                    <Text style={styles.meta}>Saved: {formatSmartPayTimestamp(entry.savedAt)}</Text>
                    {entry.receipt?.completedAt ? (
                      <Text style={styles.meta}>Completed: {formatSmartPayTimestamp(entry.receipt.completedAt)}</Text>
                    ) : null}
                    {entry.execution.error ? (
                      <Text style={styles.warning}>Error: {entry.execution.error}</Text>
                    ) : null}
                    <Text style={styles.inlineHint}>
                      {getSmartPayHistoryRestoreHint(entry, { hasAccountAuth })}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          ))}
        </View>
      ) : null}

      <View style={styles.card}>
        <Text style={styles.label}>Capabilities</Text>
        {hydrated && (intent || quote || execution || rawPayload.trim()) ? (
          <Text style={styles.persistedNote}>Restored Smart Pay draft/session from secure device storage.</Text>
        ) : null}
        {loadingCapabilities ? (
          <ActivityIndicator color="#6ee7b7" />
        ) : (
          <>
            <Text style={styles.meta}>Enabled: {capabilities?.enabled ? "yes" : "no"}</Text>
            <Text style={styles.meta}>Networks: {capabilities?.supportedNetworks?.join(", ") || "—"}</Text>
            <Text style={styles.meta}>Assets: {supportedSymbols.join(", ")}</Text>
            <Text style={styles.meta}>Max slippage: {capabilities?.maxSlippageBps ?? "—"} bps</Text>
            <Text style={styles.meta}>ACP fee reserve: {capabilities?.minAcpFeeReserve ?? "—"}</Text>
          </>
        )}
      </View>

      <View style={styles.card}>
        <Text style={styles.label}>QR / payment payload</Text>
        <TextInput
          style={[styles.input, styles.payloadInput]}
          multiline
          value={rawPayload}
          onChangeText={(value) => {
            setPayloadSource("paste");
            setRawPayload(value);
          }}
          autoCapitalize="none"
          placeholder="Paste or share ACP URI, address, or EIP-681 payload"
          placeholderTextColor="#64748b"
        />
        {payloadSource === "share" && rawPayload.trim() ? (
          <Text style={styles.persistedNote}>Shared payload draft restored into Smart Pay. Review it before parsing or executing.</Text>
        ) : null}
        <View style={styles.rowWrap}>
          <Pressable style={styles.secondary} onPress={onPaste} disabled={busy}>
            <Text style={styles.secondaryText}>Paste from clipboard</Text>
          </Pressable>
          <Pressable style={styles.secondary} onPress={onPickFromGallery} disabled={busy}>
            <Text style={styles.secondaryText}>Import QR image</Text>
          </Pressable>
          <Pressable style={styles.secondary} onPress={onOpenCamera} disabled={busy}>
            <Text style={styles.secondaryText}>Scan with camera</Text>
          </Pressable>
          <Pressable style={styles.primary} onPress={onParse} disabled={busy}>
            <Text style={styles.primaryText}>Parse</Text>
          </Pressable>
        </View>
        {intentFreshnessWarning ? <Text style={styles.warning}>{intentFreshnessWarning}</Text> : null}
      </View>

      <View style={styles.card}>
        <Text style={styles.label}>Preferred source asset</Text>
        <View style={styles.chips}>
          {supportedSymbols.map((symbol) => {
            const active = symbol === selectedAsset;
            return (
              <Pressable
                key={symbol}
                style={[styles.chip, active && styles.chipActive]}
                onPress={() => setSelectedAsset(symbol)}
              >
                <Text style={[styles.chipText, active && styles.chipTextActive]}>{symbol}</Text>
              </Pressable>
            );
          })}
        </View>
        {quoteFreshnessWarning && quote ? <Text style={styles.warning}>{quoteFreshnessWarning}</Text> : null}
        <Pressable style={styles.primary} onPress={onQuote} disabled={busy || !canRequestQuote}>
          <Text style={styles.primaryText}>Get quote</Text>
        </Pressable>
      </View>

      {intent ? (
        <View style={styles.card}>
          <Text style={styles.label}>Parsed payment intent</Text>
          <Text style={styles.value}>{intent.status} · {intent.network}</Text>
          <Text style={styles.meta}>Asset: {intent.asset.symbol || "unknown"}</Text>
          <Text style={styles.meta}>Recipient: {intent.recipient.address}</Text>
          <Text style={styles.meta}>Amount: {intent.amount?.value ?? "—"}</Text>
          <Text style={styles.meta}>Parse method: {intent.parseMethod}</Text>
          {intent.merchant?.label ? <Text style={styles.meta}>Merchant: {intent.merchant.label}</Text> : null}
          {intent.merchant?.category ? <Text style={styles.meta}>Merchant category: {intent.merchant.category}</Text> : null}
          {intent.merchant?.invoiceId ? <Text style={styles.meta}>Invoice: {intent.merchant.invoiceId}</Text> : null}
          {intent.merchant?.website ? (
            <Pressable onPress={() => void onOpenExplorerUrl(intent.merchant?.website)}>
              <Text style={styles.inlineAction}>{intent.merchant.website}</Text>
            </Pressable>
          ) : null}
          {intent.memo?.value ? <Text style={styles.meta}>Memo: {intent.memo.value}</Text> : null}
          {intentFreshnessWarning ? <Text style={styles.warning}>{intentFreshnessWarning}</Text> : null}
          {intent.warnings.length ? <Text style={styles.warning}>Warnings: {intent.warnings.join(" · ")}</Text> : null}
          {intent.riskFlags.length ? <Text style={styles.warning}>Risk flags: {intent.riskFlags.join(" · ")}</Text> : null}
        </View>
      ) : null}

      {quote ? (
        <View style={styles.card}>
          <Text style={styles.label}>Quote</Text>
          <Text style={styles.value}>{quote.mode}</Text>
          <Text style={styles.meta}>Source: {quote.requiredSourceAmount} {quote.sourceAsset.symbol}</Text>
          <Text style={styles.meta}>Target: {quote.targetAmount} {quote.targetAsset.symbol}</Text>
          <Text style={styles.meta}>Service fee: {quote.serviceFeeAcp} ACP</Text>
          <Text style={styles.meta}>{getSmartPayQuoteExpiryLabel(quote)}</Text>
          <Text style={quoteExpired ? styles.warning : styles.meta}>{getSmartPayQuoteExpiryHint(quote)}</Text>
          {quoteFreshnessWarning ? <Text style={styles.warning}>{quoteFreshnessWarning}</Text> : null}
          {quote.networkFee.map((item, index) => (
            <Text key={`${item.network}-${item.assetSymbol}-${index}`} style={styles.meta}>
              Network fee: {item.amount} {item.assetSymbol} on {item.network}
            </Text>
          ))}
          {quote.route.map((step, index) => (
            <Text key={`${step.kind}-${index}`} style={styles.meta}>
              Route {index + 1}: {step.kind} {step.fromAsset} → {step.toAsset} ({step.network})
            </Text>
          ))}
          <Pressable style={styles.primary} onPress={onOpenConfirmation} disabled={busy || !canReviewQuote}>
            <Text style={styles.primaryText}>{quoteExpired ? "Quote expired — re-quote" : quoteFreshnessWarning ? "Quote stale — re-quote" : "Review confirmation"}</Text>
          </Pressable>
        </View>
      ) : null}

      {showConfirmation && intent && quote ? (
        <View style={[styles.card, styles.confirmCard]}>
          <Text style={styles.label}>Confirmation required</Text>
          <Text style={styles.value}>Review before execute</Text>
          <Text style={styles.meta}>Destination: {intent.recipient.address}</Text>
          <Text style={styles.meta}>Target asset: {quote.targetAsset.symbol} on {quote.targetAsset.network}</Text>
          <Text style={styles.meta}>Target amount: {quote.targetAmount}</Text>
          <Text style={styles.meta}>Source spend: {quote.requiredSourceAmount} {quote.sourceAsset.symbol}</Text>
          <Text style={styles.meta}>Service fee: {quote.serviceFeeAcp} ACP</Text>
          {intent.merchant?.label ? <Text style={styles.meta}>Merchant: {intent.merchant.label}</Text> : null}
          {intent.merchant?.category ? <Text style={styles.meta}>Merchant category: {intent.merchant.category}</Text> : null}
          {intent.merchant?.invoiceId ? <Text style={styles.meta}>Invoice: {intent.merchant.invoiceId}</Text> : null}
          {intent.merchant?.website ? (
            <Pressable onPress={() => void onOpenExplorerUrl(intent.merchant?.website)}>
              <Text style={styles.inlineAction}>{intent.merchant.website}</Text>
            </Pressable>
          ) : null}
          <Text style={styles.meta}>{getSmartPayQuoteExpiryLabel(quote)}</Text>
          <Text style={quoteExpired ? styles.warning : styles.meta}>{getSmartPayQuoteExpiryHint(quote)}</Text>
          {quoteFreshnessWarning ? <Text style={styles.warning}>{quoteFreshnessWarning}</Text> : null}
          <Text style={styles.meta}>Max slippage: {quote.slippageBps} bps</Text>
          {intent.memo?.value ? <Text style={styles.meta}>Memo: {intent.memo.value}</Text> : null}
          {quote.networkFee.map((item, index) => (
            <Text key={`confirm-fee-${item.network}-${item.assetSymbol}-${index}`} style={styles.meta}>
              Network fee: {item.amount} {item.assetSymbol} on {item.network}
            </Text>
          ))}
          {quote.route.map((step, index) => (
            <Text key={`confirm-route-${step.kind}-${index}`} style={styles.meta}>
              Route {index + 1}: {step.kind} {step.fromAsset} → {step.toAsset} via {step.network}
            </Text>
          ))}
          {quote.warnings.length ? <Text style={styles.warning}>Quote warnings: {quote.warnings.join(" · ")}</Text> : null}
          {quote.riskFlags.length ? <Text style={styles.warning}>Quote risk flags: {quote.riskFlags.join(" · ")}</Text> : null}
          {intent.warnings.length ? <Text style={styles.warning}>Intent warnings: {intent.warnings.join(" · ")}</Text> : null}
          <Pressable
            style={[styles.confirmToggle, confirmationAccepted && styles.confirmToggleActive]}
            onPress={() => setConfirmationAccepted((current) => !current)}
          >
            <Text style={[styles.confirmToggleText, confirmationAccepted && styles.confirmToggleTextActive]}>
              {confirmationAccepted ? "Accepted: destination, amount, fees, and route" : "Tap to accept destination, amount, fees, and route"}
            </Text>
          </Pressable>
          <View style={styles.row}>
            <Pressable style={styles.secondary} onPress={onResetConfirmation} disabled={busy}>
              <Text style={styles.secondaryText}>Back</Text>
            </Pressable>
            <Pressable style={styles.primary} onPress={onExecute} disabled={busy || !confirmationAccepted || quoteExpired || Boolean(quoteFreshnessWarning)}>
              <Text style={styles.primaryText}>{quoteExpired ? "Quote expired" : quoteFreshnessWarning ? "Quote stale" : "Execute"}</Text>
            </Pressable>
          </View>
        </View>
      ) : null}

      {execution && activeExecutionView ? (
        <View style={styles.card}>
          <Text style={styles.label}>Execution session</Text>
          <Text style={styles.value}>{getSmartPayExecutionStatusLabel(activeExecutionView.status)}</Text>
          <Text style={styles.meta}>Execution ID: {activeExecutionView.id}</Text>
          <Text style={styles.meta}>Recoverable: {activeExecutionView.recoverable ? "yes" : "no"}</Text>
          <Text style={styles.meta}>Next action: {activeExecutionView.nextAction || "—"}</Text>
          {activeHistoryEntry ? (
            <>
              <Text style={styles.meta}>Resume access: {getSmartPayHistoryAccessLabel(activeHistoryEntry, { hasAccountAuth })}</Text>
              <Text style={styles.meta}>Recovery state: {getSmartPayHistoryRecoveryStateLabel(activeHistoryEntry, { hasAccountAuth }).replace(/^Recovery state: /, "")}</Text>
              <Text style={styles.meta}>Available actions: {getSmartPayHistoryActionLabel(activeHistoryEntry, { hasAccountAuth })}</Text>
              <Text style={styles.meta}>{getSmartPayHistoryNextStepLabel(activeHistoryEntry, { hasAccountAuth })}</Text>
              <Text style={styles.meta}>{getSmartPayHistoryAccessHint(activeHistoryEntry, { hasAccountAuth })}</Text>
              <Text style={styles.meta}>{getSmartPayHistoryRecoveryStateHint(activeHistoryEntry, { hasAccountAuth })}</Text>
              <Text style={styles.meta}>{getSmartPayHistoryActionHint(activeHistoryEntry, { hasAccountAuth })}</Text>
              <Text style={styles.meta}>{getSmartPayHistoryNextStepHint(activeHistoryEntry, { hasAccountAuth })}</Text>
            </>
          ) : null}
          <Text style={styles.meta}>Updated: {formatSmartPayTimestamp(activeExecutionView.updatedAt)}</Text>
          {activeExecutionProgressDisplayLines.length ? (
            <>
              {activeExecutionProgressDisplayLines.map((line) => (
                <Text key={line} style={styles.meta}>{line}</Text>
              ))}
            </>
          ) : null}
          {activeProgressHint ? <Text style={styles.meta}>{activeProgressHint}</Text> : null}
          {activeProgressSourceLabel ? <Text style={styles.meta}>{activeProgressSourceLabel}</Text> : null}
          {activeProgressSourceHint ? <Text style={styles.inlineHint}>{activeProgressSourceHint}</Text> : null}
          {activeHistoryEntry ? <Text style={styles.meta}>{getSmartPayHistoryProofLabel(activeHistoryEntry)}</Text> : null}
          {activeHistoryEntry ? <Text style={styles.meta}>{getSmartPayHistoryProofHint(activeHistoryEntry, { hasAccountAuth })}</Text> : null}
          {activeHistoryEntry ? <Text style={styles.meta}>{getSmartPayHistoryProofSyncLabel(activeHistoryEntry, { hasAccountAuth })}</Text> : null}
          {activeHistoryEntry ? <Text style={styles.inlineHint}>{getSmartPayHistoryProofSyncHint(activeHistoryEntry, { hasAccountAuth })}</Text> : null}
          {activeProofRouteDetailLabel ? <Text style={styles.meta}>{activeProofRouteDetailLabel}</Text> : null}
          {activeProofRouteDetailHint ? <Text style={styles.inlineHint}>{activeProofRouteDetailHint}</Text> : null}
          {activeProofQualityLabel ? <Text style={styles.meta}>{activeProofQualityLabel}</Text> : null}
          {activeProofQualityHint ? <Text style={styles.inlineHint}>{activeProofQualityHint}</Text> : null}
          {activeProofProvenanceLabel ? <Text style={styles.meta}>{activeProofProvenanceLabel}</Text> : null}
          {activeProofProvenanceHint ? <Text style={styles.inlineHint}>{activeProofProvenanceHint}</Text> : null}
          {activePendingProofHint ? <Text style={styles.inlineHint}>{activePendingProofHint}</Text> : null}
          {activeAdditionalProofHint ? <Text style={styles.inlineHint}>{activeAdditionalProofHint}</Text> : null}
          <Text style={styles.label}>Observed route proof</Text>
          {activeProofRouteSteps.length ? activeProofRouteSteps.map((step) => {
            const txRef = step.txRef;
            const txRefStorageLabel = txRef
              ? getSmartPayHistoryTxRefStorageLabel(activeHistoryEntry!, txRef)
              : null;
            const txRefStorageHint = txRef
              ? getSmartPayHistoryTxRefStorageHint(activeHistoryEntry!, txRef)
              : null;
            return (
              <View key={`execution-${step.key}`} style={styles.txRow}>
                <Text style={styles.meta}>
                  {step.status === "linked" ? "✓" : "…"} {step.label}
                </Text>
                <Text style={styles.inlineHint}>{getSmartPayHistoryProofRouteStepHint(activeHistoryEntry!, step)}</Text>
                {txRefStorageLabel ? (
                  <Text style={styles.meta}>{txRefStorageLabel}</Text>
                ) : null}
                {txRefStorageHint ? (
                  <Text style={styles.inlineHint}>{txRefStorageHint}</Text>
                ) : null}
                {txRef ? (
                  <>
                    <Text style={styles.meta}>{formatSmartPayTxRefLabel(txRef)}</Text>
                    {txRef.explorerUrl ? (
                      <Pressable onPress={() => void onOpenExplorerUrl(txRef.explorerUrl)}>
                        <Text style={styles.inlineAction}>{txRef.explorerUrl}</Text>
                      </Pressable>
                    ) : (
                      <Text style={styles.inlineHint}>Explorer link pending for this route step.</Text>
                    )}
                  </>
                ) : null}
              </View>
            );
          }) : activeLinkedProofTxRefs.length ? activeLinkedProofTxRefs.map((tx) => {
            const proofTxHint = activeHistoryEntry
              ? getSmartPayHistoryProofTxRefHint(activeHistoryEntry, tx)
              : null;
            const proofTxStorageLabel = activeHistoryEntry
              ? getSmartPayHistoryTxRefStorageLabel(activeHistoryEntry, tx)
              : null;
            const proofTxStorageHint = activeHistoryEntry
              ? getSmartPayHistoryTxRefStorageHint(activeHistoryEntry, tx)
              : null;
            return (
              <View key={`execution-linked-${tx.role}-${tx.network}-${tx.txid}`} style={styles.txRow}>
                <Text style={styles.meta}>{formatSmartPayTxRefLabel(tx)}</Text>
                {proofTxHint ? (
                  <Text style={styles.inlineHint}>{proofTxHint}</Text>
                ) : null}
                {proofTxStorageLabel ? (
                  <Text style={styles.meta}>{proofTxStorageLabel}</Text>
                ) : null}
                {proofTxStorageHint ? (
                  <Text style={styles.inlineHint}>{proofTxStorageHint}</Text>
                ) : null}
                {tx.explorerUrl ? (
                  <Pressable onPress={() => void onOpenExplorerUrl(tx.explorerUrl)}>
                    <Text style={styles.inlineAction}>{tx.explorerUrl}</Text>
                  </Pressable>
                ) : (
                  <Text style={styles.inlineHint}>Explorer link pending for this tx reference.</Text>
                )}
              </View>
            );
          }) : activeExecutionTxRefs.length ? activeExecutionTxRefs.map((tx) => {
            const proofTxHint = activeHistoryEntry
              ? getSmartPayHistoryProofTxRefHint(activeHistoryEntry, tx)
              : null;
            const proofTxStorageLabel = activeHistoryEntry
              ? getSmartPayHistoryTxRefStorageLabel(activeHistoryEntry, tx)
              : null;
            const proofTxStorageHint = activeHistoryEntry
              ? getSmartPayHistoryTxRefStorageHint(activeHistoryEntry, tx)
              : null;
            return (
              <View key={`${tx.role}-${tx.network}-${tx.txid}`} style={styles.txRow}>
                <Text style={styles.meta}>{formatSmartPayTxRefLabel(tx)}</Text>
                {proofTxHint ? (
                  <Text style={styles.inlineHint}>{proofTxHint}</Text>
                ) : null}
                {proofTxStorageLabel ? (
                  <Text style={styles.meta}>{proofTxStorageLabel}</Text>
                ) : null}
                {proofTxStorageHint ? (
                  <Text style={styles.inlineHint}>{proofTxStorageHint}</Text>
                ) : null}
                {tx.explorerUrl ? (
                  <Pressable onPress={() => void onOpenExplorerUrl(tx.explorerUrl)}>
                    <Text style={styles.inlineAction}>{tx.explorerUrl}</Text>
                  </Pressable>
                ) : (
                  <Text style={styles.inlineHint}>Explorer link pending for this tx reference.</Text>
                )}
              </View>
            );
          }) : <Text style={styles.meta}>{getSmartPayHistoryProofEmptyStateHint(activeHistoryEntry)}</Text>}
          {activeAdditionalProofTxRefs.length ? (
            <>
              <Text style={styles.label}>Additional observed tx refs</Text>
              {activeAdditionalProofProvenanceLabel ? (
                <Text style={styles.meta}>{activeAdditionalProofProvenanceLabel}</Text>
              ) : null}
              {activeAdditionalProofProvenanceHint ? (
                <Text style={styles.inlineHint}>{activeAdditionalProofProvenanceHint}</Text>
              ) : null}
              {activeAdditionalProofTxRefs.map((tx) => {
                const additionalProofHint = getSmartPayHistoryAdditionalProofTxRefHint(activeHistoryEntry!, tx);
                const additionalProofStorageLabel = getSmartPayHistoryTxRefStorageLabel(activeHistoryEntry!, tx);
                const additionalProofStorageHint = getSmartPayHistoryTxRefStorageHint(activeHistoryEntry!, tx);
                return (
                  <View key={`execution-extra-${tx.role}-${tx.network}-${tx.txid}`} style={styles.txRow}>
                    <Text style={styles.meta}>{formatSmartPayTxRefLabel(tx)}</Text>
                    {additionalProofHint ? (
                      <Text style={styles.inlineHint}>{additionalProofHint}</Text>
                    ) : null}
                    {additionalProofStorageLabel ? (
                      <Text style={styles.meta}>{additionalProofStorageLabel}</Text>
                    ) : null}
                    {additionalProofStorageHint ? (
                      <Text style={styles.inlineHint}>{additionalProofStorageHint}</Text>
                    ) : null}
                    {tx.explorerUrl ? (
                      <Pressable onPress={() => void onOpenExplorerUrl(tx.explorerUrl)}>
                        <Text style={styles.inlineAction}>{tx.explorerUrl}</Text>
                      </Pressable>
                    ) : (
                      <Text style={styles.inlineHint}>Explorer link pending for this tx reference.</Text>
                    )}
                  </View>
                );
              })}
            </>
          ) : null}
          {!canRefreshExecution ? (
            <Text style={styles.warning}>
              {getSmartPayRefreshOrRecoverHint({
                sessionToken: activeSessionToken,
                hasAccountAuth,
              })}
            </Text>
          ) : null}
          {!canRefreshExecution && !hasAccountAuth ? (
            <Text style={styles.inlineHint}>
              This Expo build is not configured with an ANCAP Authorization header, so authenticated backend resume/history is unavailable here even though the backend contract supports it.
            </Text>
          ) : null}
          {!canRecoverExecution ? (
            <Text style={styles.inlineHint}>
              {getSmartPayRecoverHint({
                sessionToken: activeSessionToken,
                hasAccountAuth,
                recoverable: activeExecutionView.recoverable,
              })}
            </Text>
          ) : null}
          <Text style={styles.label}>{activeHistoryEntry ? getSmartPayHistoryRecoveryInputLabel(activeHistoryEntry) : "Recovery tx hints (optional)"}</Text>
          <Text style={styles.inlineHint}>
            {activeHistoryEntry
              ? getSmartPayHistoryRecoveryInputHint(activeHistoryEntry)
              : "Paste observed route tx hashes or explorer links from the original signing device if refresh alone is not enough. Smart Pay recover will normalize known tx ids and map them onto quoted route steps in order."}
          </Text>
          <TextInput
            style={[styles.input, styles.payloadInput, styles.recoveryInput]}
            multiline
            value={recoveryDraftTxs}
            onChangeText={setRecoveryDraftTxs}
            autoCapitalize="none"
            autoCorrect={false}
            placeholder="One tx hash per line, comma, or space"
            placeholderTextColor="#64748b"
          />
          {recoveryDraftTxs.trim() ? (
            <>
              <Text style={styles.meta}>
                Parsed recovery txs: {parsedRecoveryTxs.length}
              </Text>
              {parsedRecoveryInput.refs.length ? parsedRecoveryInput.refs.map((ref, index) => (
                <Text key={`recovery-ref-${ref.txid}-${index}`} style={styles.inlineHint}>
                  {formatSmartPayRecoveryRefPreview(ref)}
                </Text>
              )) : null}
              {parsedRecoveryInput.duplicateTokens.length ? (
                <Text style={styles.inlineHint}>
                  Ignored duplicates: {parsedRecoveryInput.duplicateTokens.join(", ")}
                </Text>
              ) : null}
              {parsedRecoveryInput.invalidTokens.length ? (
                <Text style={styles.warning}>
                  Could not parse as tx hash or explorer link: {parsedRecoveryInput.invalidTokens.join(", ")}
                </Text>
              ) : null}
              {recoveryInputBlockReason ? (
                <Text style={styles.warning}>{recoveryInputBlockReason}</Text>
              ) : null}
            </>
          ) : (
            <Text style={styles.inlineHint}>Leave empty to ask the backend for a status-only recovery pass.</Text>
          )}
          <View style={styles.row}>
            <Pressable style={styles.secondary} onPress={onRefreshExecution} disabled={busy || !canRefreshExecution}>
              <Text style={styles.secondaryText}>{activeHistoryEntry ? getSmartPayHistoryRefreshButtonLabel(activeHistoryEntry, { hasAccountAuth }) : "Refresh status"}</Text>
            </Pressable>
            <Pressable style={styles.secondary} onPress={onRecover} disabled={busy || !canRecoverExecution || !canSubmitRecoveryInput}>
              <Text style={styles.secondaryText}>
                {activeHistoryEntry
                  ? getSmartPayHistoryRecoverButtonLabel(activeHistoryEntry, parsedRecoveryInput.refs.length)
                  : "Recover"}
              </Text>
            </Pressable>
          </View>
        </View>
      ) : null}

      {execution && intent && activeHistoryEntry && activeReceiptDisplay ? (
        <View style={styles.card}>
          <Text style={styles.label}>{getSmartPayHistorySnapshotTitle(activeHistoryEntry)}</Text>
          <Text style={styles.value}>{activeReceiptDisplay.targetAmount} {activeReceiptDisplay.targetAsset}</Text>
          <Text style={styles.meta}>Recipient: {activeReceiptDisplay.recipientAddress}</Text>
          <Text style={styles.meta}>Source asset: {activeReceiptDisplay.sourceAsset}</Text>
          <Text style={styles.meta}>Source spend: {activeReceiptDisplay.sourceAmount}</Text>
          <Text style={styles.meta}>Service fee: {activeReceiptDisplay.serviceFeeAcp} ACP</Text>
          <Text style={styles.meta}>{getSmartPayHistorySnapshotStatusLabel(activeHistoryEntry)}: {getSmartPayExecutionStatusLabel(activeExecutionView?.status ?? execution.status)}</Text>
          <Text style={styles.meta}>History source: {getSmartPayHistorySourceLabel(activeHistoryEntry)}</Text>
          <Text style={styles.meta}>{getSmartPayHistorySourceHint(activeHistoryEntry)}</Text>
          <Text style={styles.meta}>{getSmartPayHistoryFreshnessLabel(activeHistoryEntry)}</Text>
          <Text style={styles.meta}>{getSmartPayHistoryFreshnessHint(activeHistoryEntry, { hasAccountAuth })}</Text>
          <Text style={styles.meta}>Resume access: {getSmartPayHistoryAccessLabel(activeHistoryEntry, { hasAccountAuth })}</Text>
          <Text style={styles.meta}>Recovery state: {getSmartPayHistoryRecoveryStateLabel(activeHistoryEntry, { hasAccountAuth }).replace(/^Recovery state: /, "")}</Text>
          <Text style={styles.meta}>Available actions: {getSmartPayHistoryActionLabel(activeHistoryEntry, { hasAccountAuth })}</Text>
          <Text style={styles.meta}>{getSmartPayHistoryNextStepLabel(activeHistoryEntry, { hasAccountAuth })}</Text>
          <Text style={styles.meta}>{getSmartPayHistoryAccessHint(activeHistoryEntry, { hasAccountAuth })}</Text>
          <Text style={styles.meta}>{getSmartPayHistoryRecoveryStateHint(activeHistoryEntry, { hasAccountAuth })}</Text>
          <Text style={styles.meta}>{getSmartPayHistoryActionHint(activeHistoryEntry, { hasAccountAuth })}</Text>
          <Text style={styles.meta}>{getSmartPayHistoryNextStepHint(activeHistoryEntry, { hasAccountAuth })}</Text>
          {activeExecutionProgressDisplayLines.length ? activeExecutionProgressDisplayLines.map((line) => (
            <Text key={`receipt-progress-${line}`} style={styles.meta}>{line}</Text>
          )) : null}
          {activeProgressHint ? <Text style={styles.meta}>{activeProgressHint}</Text> : null}
          {activeProgressSourceLabel ? <Text style={styles.meta}>{activeProgressSourceLabel}</Text> : null}
          {activeProgressSourceHint ? <Text style={styles.inlineHint}>{activeProgressSourceHint}</Text> : null}
          <Text style={styles.meta}>{getSmartPayHistoryProofLabel(activeHistoryEntry)}</Text>
          <Text style={styles.meta}>{getSmartPayHistoryProofHint(activeHistoryEntry, { hasAccountAuth })}</Text>
          {activeProofRouteDetailLabel ? <Text style={styles.meta}>{activeProofRouteDetailLabel}</Text> : null}
          {activeProofRouteDetailHint ? <Text style={styles.inlineHint}>{activeProofRouteDetailHint}</Text> : null}
          {activeProofProvenanceLabel ? <Text style={styles.meta}>{activeProofProvenanceLabel}</Text> : null}
          {activeProofProvenanceHint ? <Text style={styles.inlineHint}>{activeProofProvenanceHint}</Text> : null}
          {activePendingProofHint ? <Text style={styles.inlineHint}>{activePendingProofHint}</Text> : null}
          {activeAdditionalProofHint ? <Text style={styles.inlineHint}>{activeAdditionalProofHint}</Text> : null}
          {activeReceiptDisplay.completedAt ? <Text style={styles.meta}>Completed at: {formatSmartPayTimestamp(activeReceiptDisplay.completedAt)}</Text> : null}
          {activeReceiptDisplay.merchantLabel ? <Text style={styles.meta}>Merchant: {activeReceiptDisplay.merchantLabel}</Text> : null}
          {activeReceiptDisplay.merchantCategory ? <Text style={styles.meta}>Merchant category: {activeReceiptDisplay.merchantCategory}</Text> : null}
          {activeReceiptDisplay.merchantInvoiceId ? <Text style={styles.meta}>Invoice: {activeReceiptDisplay.merchantInvoiceId}</Text> : null}
          {activeReceiptDisplay.merchantWebsite ? (
            <Pressable onPress={() => void onOpenExplorerUrl(activeReceiptDisplay.merchantWebsite)}>
              <Text style={styles.inlineAction}>{activeReceiptDisplay.merchantWebsite}</Text>
            </Pressable>
          ) : null}
          {getSmartPayHistoryMerchantHint(activeReceiptDisplay) ? (
            <Text style={styles.inlineHint}>{getSmartPayHistoryMerchantHint(activeReceiptDisplay)}</Text>
          ) : null}
          {activeExecutionView?.error ? <Text style={styles.warning}>Execution error: {activeExecutionView.error}</Text> : null}
          <Text style={styles.label}>Route summary</Text>
          {activeReceiptDisplay.routeSummary.length ? activeReceiptDisplay.routeSummary.map((line, index) => (
            <Text key={`receipt-route-${index}`} style={styles.meta}>
              {line}
            </Text>
          )) : <Text style={styles.meta}>No route summary available yet.</Text>}
          <Text style={styles.label}>{getSmartPayHistoryNetworkFeesLabel(activeReceiptDisplay)}</Text>
          {getSmartPayHistoryNetworkFeesHint(activeReceiptDisplay) ? (
            <Text style={styles.inlineHint}>{getSmartPayHistoryNetworkFeesHint(activeReceiptDisplay)}</Text>
          ) : null}
          {activeReceiptDisplay.networkFees.length ? activeReceiptDisplay.networkFees.map((fee, index) => (
            <Text key={`receipt-fee-${fee.network}-${fee.assetSymbol}-${index}`} style={styles.meta}>
              {fee.amount} {fee.assetSymbol} on {fee.network}
            </Text>
          )) : <Text style={styles.meta}>No network fees reported.</Text>}
          <Text style={styles.label}>Route proof coverage</Text>
          <Text style={styles.meta}>{getSmartPayHistoryProofLabel(activeHistoryEntry)}</Text>
          <Text style={styles.inlineHint}>{getSmartPayHistoryProofHint(activeHistoryEntry, { hasAccountAuth })}</Text>
          <Text style={styles.meta}>{getSmartPayHistoryProofSyncLabel(activeHistoryEntry, { hasAccountAuth })}</Text>
          <Text style={styles.inlineHint}>{getSmartPayHistoryProofSyncHint(activeHistoryEntry, { hasAccountAuth })}</Text>
          {activeProofRouteDetailLabel ? (
            <Text style={styles.meta}>{activeProofRouteDetailLabel}</Text>
          ) : null}
          {activeProofRouteDetailHint ? (
            <Text style={styles.inlineHint}>{activeProofRouteDetailHint}</Text>
          ) : null}
          {activeProofQualityLabel ? (
            <Text style={styles.meta}>{activeProofQualityLabel}</Text>
          ) : null}
          {activeProofQualityHint ? (
            <Text style={styles.inlineHint}>{activeProofQualityHint}</Text>
          ) : null}
          {activeProofProvenanceLabel ? (
            <Text style={styles.meta}>{activeProofProvenanceLabel}</Text>
          ) : null}
          {activeProofProvenanceHint ? (
            <Text style={styles.inlineHint}>{activeProofProvenanceHint}</Text>
          ) : null}
          {activePendingProofHint ? (
            <Text style={styles.inlineHint}>{activePendingProofHint}</Text>
          ) : null}
          {activeProofRouteSteps.length ? activeProofRouteSteps.map((step) => {
            const txRef = step.txRef;
            const txRefStorageLabel = txRef
              ? getSmartPayHistoryTxRefStorageLabel(activeHistoryEntry, txRef)
              : null;
            const txRefStorageHint = txRef
              ? getSmartPayHistoryTxRefStorageHint(activeHistoryEntry, txRef)
              : null;
            return (
              <View key={step.key} style={styles.txRow}>
                <Text style={styles.meta}>
                  {step.status === "linked" ? "✓" : "…"} {step.label}
                </Text>
                <Text style={styles.inlineHint}>{getSmartPayHistoryProofRouteStepHint(activeHistoryEntry, step)}</Text>
                {txRefStorageLabel ? (
                  <Text style={styles.meta}>{txRefStorageLabel}</Text>
                ) : null}
                {txRefStorageHint ? (
                  <Text style={styles.inlineHint}>{txRefStorageHint}</Text>
                ) : null}
                {txRef ? (
                  <>
                    <Text style={styles.meta}>{formatSmartPayTxRefLabel(txRef)}</Text>
                    {txRef.explorerUrl ? (
                      <Pressable onPress={() => void onOpenExplorerUrl(txRef.explorerUrl)}>
                        <Text style={styles.inlineAction}>{txRef.explorerUrl}</Text>
                      </Pressable>
                    ) : (
                      <Text style={styles.inlineHint}>Explorer link pending for this route step.</Text>
                    )}
                  </>
                ) : null}
              </View>
            );
          }) : activeLinkedProofTxRefs.length ? activeLinkedProofTxRefs.map((tx) => {
            const proofTxHint = getSmartPayHistoryProofTxRefHint(activeHistoryEntry, tx);
            const proofTxStorageLabel = getSmartPayHistoryTxRefStorageLabel(activeHistoryEntry, tx);
            const proofTxStorageHint = getSmartPayHistoryTxRefStorageHint(activeHistoryEntry, tx);
            return (
              <View key={`receipt-${tx.role}-${tx.txid}`} style={styles.txRow}>
                <Text style={styles.meta}>{formatSmartPayTxRefLabel(tx)}</Text>
                {proofTxHint ? (
                  <Text style={styles.inlineHint}>{proofTxHint}</Text>
                ) : null}
                {proofTxStorageLabel ? (
                  <Text style={styles.meta}>{proofTxStorageLabel}</Text>
                ) : null}
                {proofTxStorageHint ? (
                  <Text style={styles.inlineHint}>{proofTxStorageHint}</Text>
                ) : null}
                {tx.explorerUrl ? (
                  <Pressable onPress={() => void onOpenExplorerUrl(tx.explorerUrl)}>
                    <Text style={styles.inlineAction}>{tx.explorerUrl}</Text>
                  </Pressable>
                ) : (
                  <Text style={styles.inlineHint}>Explorer link pending for this tx reference.</Text>
                )}
              </View>
            );
          }) : <Text style={styles.meta}>{getSmartPayHistoryProofEmptyStateHint(activeHistoryEntry)}</Text>}
          {activeAdditionalProofTxRefs.length ? (
            <>
              <Text style={styles.label}>Additional observed tx refs</Text>
              {activeAdditionalProofProvenanceLabel ? (
                <Text style={styles.meta}>{activeAdditionalProofProvenanceLabel}</Text>
              ) : null}
              {activeAdditionalProofProvenanceHint ? (
                <Text style={styles.inlineHint}>{activeAdditionalProofProvenanceHint}</Text>
              ) : null}
              {activeAdditionalProofTxRefs.map((tx) => {
                const additionalProofHint = getSmartPayHistoryAdditionalProofTxRefHint(activeHistoryEntry, tx);
                const additionalProofStorageLabel = getSmartPayHistoryTxRefStorageLabel(activeHistoryEntry, tx);
                const additionalProofStorageHint = getSmartPayHistoryTxRefStorageHint(activeHistoryEntry, tx);
                return (
                  <View key={`receipt-extra-${tx.role}-${tx.network}-${tx.txid}`} style={styles.txRow}>
                    <Text style={styles.meta}>{formatSmartPayTxRefLabel(tx)}</Text>
                    {additionalProofHint ? (
                      <Text style={styles.inlineHint}>{additionalProofHint}</Text>
                    ) : null}
                    {additionalProofStorageLabel ? (
                      <Text style={styles.meta}>{additionalProofStorageLabel}</Text>
                    ) : null}
                    {additionalProofStorageHint ? (
                      <Text style={styles.inlineHint}>{additionalProofStorageHint}</Text>
                    ) : null}
                    {tx.explorerUrl ? (
                      <Pressable onPress={() => void onOpenExplorerUrl(tx.explorerUrl)}>
                        <Text style={styles.inlineAction}>{tx.explorerUrl}</Text>
                      </Pressable>
                    ) : (
                      <Text style={styles.inlineHint}>Explorer link pending for this tx reference.</Text>
                    )}
                  </View>
                );
              })}
            </>
          ) : null}
        </View>
      ) : null}

      {error ? <Text style={styles.error}>{error}</Text> : null}
      {busy ? <ActivityIndicator color="#6ee7b7" style={{ marginTop: 12 }} /> : null}

      <Modal visible={showCamera} animationType="slide" onRequestClose={() => setShowCamera(false)}>
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Scan QR</Text>
            <Pressable style={styles.modalClose} onPress={() => setShowCamera(false)}>
              <Text style={styles.modalCloseText}>Close</Text>
            </Pressable>
          </View>
          <CameraView
            style={styles.camera}
            barcodeScannerSettings={{ barcodeTypes: ["qr"] }}
            onBarcodeScanned={({ data }) => onCameraScanned({ data })}
          />
          <Text style={styles.modalHint}>Point camera at ACP / EIP-681 QR code.</Text>
        </View>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, flexGrow: 1 },
  title: { color: "#f5f7ff", fontSize: 22, fontWeight: "700", marginBottom: 8 },
  subtitle: { color: "#94a3b8", lineHeight: 20, marginBottom: 20 },
  card: {
    backgroundColor: "#111827",
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderColor: "#1e293b",
    borderWidth: 1,
  },
  confirmCard: {
    borderColor: "#f59e0b",
  },
  label: { color: "#94a3b8", marginBottom: 8 },
  value: { color: "#6ee7b7", fontSize: 18, fontWeight: "600", marginBottom: 8 },
  meta: { color: "#cbd5e1", marginTop: 4, fontSize: 13 },
  warning: { color: "#fbbf24", marginTop: 8, fontSize: 13 },
  persistedNote: { color: "#93c5fd", marginBottom: 10, fontSize: 13 },
  input: {
    backgroundColor: "#0f172a",
    borderColor: "#334155",
    borderWidth: 1,
    borderRadius: 10,
    color: "#f5f7ff",
    padding: 12,
  },
  payloadInput: { minHeight: 120, textAlignVertical: "top" },
  recoveryInput: { minHeight: 88 },
  topActions: { marginBottom: 16 },
  sectionHeaderRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 },
  row: { flexDirection: "row", gap: 12, marginTop: 12 },
  rowWrap: { flexDirection: "row", gap: 12, marginTop: 12, flexWrap: "wrap" },
  chips: { flexDirection: "row", gap: 8, flexWrap: "wrap", marginBottom: 12 },
  chip: {
    borderWidth: 1,
    borderColor: "#334155",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  chipActive: {
    backgroundColor: "#10b981",
    borderColor: "#10b981",
  },
  chipText: { color: "#cbd5e1", fontWeight: "600" },
  chipTextActive: { color: "#042f1a" },
  historyOverviewCard: {
    marginTop: 12,
    borderColor: "#1f2937",
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    backgroundColor: "#0f172a",
  },
  historyOverviewTitle: { color: "#e2e8f0", fontWeight: "700", marginBottom: 4 },
  historySection: { marginTop: 14 },
  historySectionTitle: { color: "#e2e8f0", fontWeight: "700", marginBottom: 4 },
  historyItem: {
    marginTop: 12,
    borderColor: "#334155",
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    backgroundColor: "#0b1220",
  },
  historyRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: 12 },
  historyTitle: { color: "#f8fafc", fontWeight: "700", marginBottom: 6, flex: 1 },
  statusBadge: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  statusBadgeInFlight: { backgroundColor: "#1d4ed8" },
  statusBadgeAttention: { backgroundColor: "#b91c1c" },
  statusBadgeCompleted: { backgroundColor: "#047857" },
  statusBadgeText: { color: "#f8fafc", fontSize: 11, fontWeight: "700" },
  inlineAction: { color: "#93c5fd", fontWeight: "600" },
  inlineHint: { color: "#94a3b8", marginTop: 6, fontSize: 12 },
  txRow: { marginTop: 6 },
  confirmToggle: {
    marginTop: 14,
    borderWidth: 1,
    borderColor: "#475569",
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 14,
    backgroundColor: "#0f172a",
  },
  confirmToggleActive: {
    borderColor: "#10b981",
    backgroundColor: "#052e25",
  },
  confirmToggleText: {
    color: "#e2e8f0",
    textAlign: "center",
    fontWeight: "600",
  },
  confirmToggleTextActive: {
    color: "#6ee7b7",
  },
  secondary: {
    flex: 1,
    borderColor: "#334155",
    borderWidth: 1,
    paddingVertical: 14,
    borderRadius: 12,
  },
  secondaryText: { color: "#f5f7ff", textAlign: "center", fontWeight: "600" },
  primary: {
    flex: 1,
    backgroundColor: "#10b981",
    paddingVertical: 14,
    borderRadius: 12,
  },
  primaryText: { color: "#042f1a", textAlign: "center", fontWeight: "700" },
  error: { color: "#f87171", marginTop: 8 },
  modalContainer: { flex: 1, backgroundColor: "#020617", paddingTop: 56, paddingHorizontal: 20 },
  modalHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 16 },
  modalTitle: { color: "#f8fafc", fontSize: 20, fontWeight: "700" },
  modalClose: {
    borderColor: "#334155",
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  modalCloseText: { color: "#f8fafc", fontWeight: "600" },
  camera: { flex: 1, borderRadius: 16, overflow: "hidden" },
  modalHint: { color: "#94a3b8", marginTop: 16, marginBottom: 24, textAlign: "center" },
});
