import json
from pathlib import Path
import shutil
import subprocess
import unittest


class FrontendGuardTests(unittest.TestCase):
    def preserved(self,before,after):
        result=subprocess.run([shutil.which('node'),str(Path(__file__).with_name('frontend_test_guard.cjs'))],
                              input=json.dumps(dict(before=before,after=after)),text=True,capture_output=True,check=True)
        return json.loads(result.stdout)['preserved']

    def test_additive_assertions_and_renamed_title_preserve_tests(self):
        before='describe("suite",()=>{it("old",async()=>{mock();await expect(run(1)).rejects.toThrow("bad");});});'
        after='describe("suite",()=>{it("expanded",async()=>{mock();await expect(run(1)).rejects.toThrow("bad");await expect(run(2)).rejects.toThrow("bad");});it("new",()=>{expect(run(3)).toBe(3);});});'
        self.assertTrue(self.preserved(before,after))

    def test_removed_assertions_skips_matcher_and_setup_changes_are_rejected(self):
        before='describe("suite",()=>{it("old",()=>{mock();expect(run(1)).toBe(2);});});'
        for after in [before.replace('expect(run(1)).toBe(2);',''),before.replace('it(', 'it.skip('),
                      before.replace('toBe(2)','toBeTruthy()'),before.replace('mock();','otherMock();'),
                      before.replace('it("old",()=>{mock();expect(run(1)).toBe(2);});','')]:
            with self.subTest(after=after):self.assertFalse(self.preserved(before,after))

    def test_each_inputs_can_expand_but_not_shrink(self):
        before='it.each([null,"", "NaN"])("invalid %s",value=>expect(run(value)).toBeNull());'
        self.assertTrue(self.preserved(before,before.replace('"NaN"]','"NaN","Infinity"]')))
        self.assertFalse(self.preserved(before,before.replace('null,','')))

    def test_formatting_and_quotes_do_not_remove_checks(self):
        self.assertTrue(self.preserved('it("old",()=>{expect(run()).toBe(2);});',"it('old', () => {\n expect(run()).toBe(2);\n});"))


if __name__=='__main__':unittest.main()
